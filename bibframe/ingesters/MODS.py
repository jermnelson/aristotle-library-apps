"""
 Module takes a MODS xml document and ingests into Redis Library Services
 Platform's BIBFRAME LinkedData models.

 This module uses the following rule chaining to create BIBFRAME entities:
 MODS->MARC21->BIBFRAME using the MODStoMARC mapping at
 http://www.loc.gov/standards/mods/v3/mods2marc-mapping.html
 and the MARC21toBIBFRAME mapping at bibframe.org. Additional MODS elements
 are mapped directly to BIBFRAME if there are not equalivant mappings.
"""
__author__ = "Jeremy Nelson"

import lxml.etree as etree
import urllib2
from aristotle.settings import REDIS_DATASTORE
from bibframe.classifiers import simple_fuzzy
from bibframe.ingesters.Ingester import personal_name_parser, Ingester
from bibframe.ingesters.Ingester import HONORIFIC_PREFIXES, HONORIFIC_SUFFIXES
from bibframe.models import Annotation, Organization, Work, Holding, Instance 
from bibframe.models import Person, Audio, Book, Cartography, LanguageMaterial
from bibframe.models import MixedMaterial, MovingImage, MusicalAudio
from bibframe.models import NonmusicalAudio, NotatedMusic 
from bibframe.models import SoftwareOrMultimedia, StillImage, TitleEntity
from bibframe.models import ThreeDimensionalObject
from person_authority.redis_helpers import get_or_generate_person
from title_search.redis_helpers import index_title
from rdflib import Namespace


MODS_NS = Namespace('http://www.loc.gov/mods/v3')

class MODSIngesterError(Exception):
    "Exception for any errors ingesting MODS into RLSP"

    def __init__(self, value):
        "Initializes Class"
        super(MODSIngesterError, self).__init__()
        self.value = value

    def __str__(self):
        "Returns string representation of Exception"
        return repr(self.value)

class MODSIngester(Ingester):
    "Class ingests MODS XML files into RLSP"

    def __init__(self, **kwargs):
        "Class takes standard RLSP BIBFRAME ingester"
        super(MODSIngester, self).__init__(**kwargs)
        self.work_class = kwargs.get('work_class',
                                     None)
        self.classifier = kwargs.get('classifier',
                                     simple_fuzzy.WorkClassifier)
        self.contributors = []
        self.creators = []
        self.instances = []
        self.mods_xml = None

    def __classify_work_class__(self):
        "Helper function classifies a work based on typeOfResource"
        if self.work_class is not None:
            return
        type_of_resource = self.mods_xml.find(
            "{{{0}}}typeOfResource".format(MODS_NS))
        type_of = type_of_resource.text
        # List of enumerated typeOfResource comes from the following website:
        # http://www.loc.gov/standards/mods/mods-outline.html#typeOfResource
        if type_of == "text":
            self.work_class = LanguageMaterial
        elif type_of == "cartographic":
            self.work_class = Cartography
        elif type_of == "notated music":
            self.work_class = NotatedMusic
        elif type_of == "sound recording-musical":
            self.work_class = MusicalAudio
        elif type_of == "sound recording-nonmusical":
            self.work_class = NonmusicalAudio
        elif type_of == "sound recording":
            self.work_class = Audio
        elif type_of == "still image":
            self.work_class = StillImage
        elif type_of == "moving image":
            self.work_class = MovingImage
        elif type_of== "three dimensional object":
            self.work_class = ThreeDimensionalObject
        elif type_of == "software, multimedia":
            self.work_class = SoftwareOrMultimedia
        elif type_of == "mixed material":
            self.work_class = MixedMaterial
        else:
            self.work_class = Work
                             
    def __create_instances__(self, work_key):
        """Helper function creates specific instance(s) from MODS

        Parameter:
        work_key -- Work Key to be associated with BIBFRAME Instance(s)
        """
        # Create an instance for each originInfo element in MODS
        origin_infos = self.mods_xml.findall('{{{0}}}originInfo'.format(
            MODS_NS))
        form = self.mods_xml.find(
            '{{{0}}}physicalDescription/{{{0}}}form'.format(MODS_NS))
        
        for element in origin_infos:
            instance_of = {'instanceOf': work_key}
            if form is not None:
                if form.attrib.get('type', None) == 'carrier':
                    if form.attrib.get('authority', None) == 'rdacarrier':
                        instance_of['rda:carrierTypeManifestation'] = form.text
            extent = element.find('{{{0}}}extent'.format(MODS_NS))
            if extent is not None:
                if extent.text is not None:
                    instance_of['extent'] = extent.text
            hdl = self.__extract_hdl__()
            if hdl is not None:
                instance_of['hdl'] = hdl
            new_instance = Instance(redis_datastore=self.redis_datastore,
                                    **instance_of)
            new_instance.save()
            self.instances.append(new_instance.redis_key)


    def __extract_person__(self, name_parts):
        """Helper method takes a list of nameParts and extracts info

        Parameter:
        name_parts -- List of namePart elements
        """
        person = dict()
        # Assumes multiple nameParts use type attribute
        # to parse out specifics
        for row in name_parts:
            name_type = row.attrib.get('type', None)
            if row.text is None:
                continue
            name_value = row.text.strip()
            if name_type == 'given':
                person['schema:givenName'] = name_value
            elif name_type == 'family':
                person['schema:familyName'] = name_value
            elif name_type == 'date':
                person['rdf:dateOfBirth'] = name_value
            elif name_type == 'termsOfAddress':
                name_value = row.text
                if HONORIFIC_PREFIXES.count(name_value) > 0:
                    person['schema:honorificPrefix'] = \
                                                     name_value
                elif HONORIFIC_SUFFIXES.count(name_value) > 1:
                    person['honorificSuffix'] = name_value
            # No type given tries parsing name and update
            # person dict if key doesn't exist
            else:
                result = personal_name_parser(row.text)
                for key, value in result.iteritems():
                    if not person.has_key(key):
                        # Filter for embedded editor values
                        if value.count('editor') > 0:
                            person['resourceRole:edt'] = value
                        else:
                            person[key] = value
            # Create an rda:rda:preferredNameForThePerson if it doesn't
            # exist
            if person.has_key("rda:preferredNameForThePerson") is False:
                person["rda:preferredNameForThePerson"] = "{1}, {0}".format(
                    person.get('schema:givenName', ''),
                    person.get('schema:familyName', ''))
                if person.has_key('schema:honorificPrefix'):
                    person["rda:preferredNameForThePerson"] = "{0}. {1}".format(
                        person['schema:honorificPrefix'],
                        person["rda:preferredNameForThePerson"])
                if person.has_key('honorificSuffix'):
                    person["rda:preferredNameForThePerson"] = "{0} {1}".format(
                        person["rda:preferredNameForThePerson"],
                        person['honorificSuffix'])
                if person.has_key('rdf:dateOfBirth'):
                    person["rda:preferredNameForThePerson"] = "{0}, {1}-".format(
                        person["rda:preferredNameForThePerson"],
                        person['rdf:dateOfBirth'])
                if person.has_key('rdf:dateOfDeath'):
                    person["rda:preferredNameForThePerson"] = "{0}{1}".format(
                        person["rda:preferredNameForThePerson"],
                        person['rdf:dateOfDeath'])
        return person
            
            
    def __extract_persons__(self):
        "Helper function extracts all creators from MODS xml"
        names = self.mods_xml.findall('{{{0}}}name'.format(MODS_NS))
        for name in names:
            person = None
            name_parts = name.findall('{{{0}}}namePart'.format(MODS_NS))
            if len(name_parts) < 1:
                continue
            # Checks role/roleTerm to see if role is a creator
            role = name.find('{{{0}}}role/{{{0}}}roleTerm'.format(MODS_NS))
            if role is None:
                continue
            person = self.__extract_person__(name_parts)
            if len(person) < 1:
                continue
            result = get_or_generate_person(person,
                                            self.redis_datastore)
            if role.text == 'creator':
                person_group = self.creators
            elif role.text == 'contributor':
                person_group = self.contributors
            else:
                # Add more roles as they are needed
                continue
            if type(result) == list:
                for person in result:
                    person_group.append(person)
            elif type(result) == Person:
                person_group.append(result)
            
                

    def __extract_hdl__(self):
        location_urls = self.mods_xml.findall('{{{0}}}location/{{{0}}}url'.format(
            MODS_NS))
        for url in location_urls:
            if url.text.startswith('http://hdl'):
                return url.text
                    
                                              

    def __extract_title__(self):
        "Helper function extracts title information from MODS"
        title_entities = []
        titleInfos = self.mods_xml.findall('{{{0}}}titleInfo'.format(MODS_NS))
        for titleInfo in titleInfos:
            output = {}
            if titleInfo.attrib.get('type')is None:
                # equalvant to MARC 245 $a
                titleValue = titleInfo.find('{{{0}}}title'.format(MODS_NS))
                if titleValue is not None and len(titleValue.text) > 0:
                    output['titleValue'] = titleValue.text
                    output['label'] = output['titleValue']
                # equalvant to MARC 245 $b
                subtitle = titleInfo.find('{{{0}}}subTitle'.format(MODS_NS))
                if subtitle is not None and len(subtitle.text) > 0:
                    output['subtitle'] = subtitle.text
                    output['label'] = '{0}: {1}'.format(output.get('label'),
                                                        output['subtitle'])
                # equalivant to MARC 245 $p
                partTitle = titleInfo.find('{{{0}}}partName'.format(MODS_NS))
                if partTitle is not None and len(partTitle.text) > 0:
                    output['partTitle'] = partTitle.text
            if len(output) > 0:
                title_entity = TitleEntity(redis_datastore=self.redis_datastore,
                                           **output)
                title_entity.save()
                index_title(title_entity, self.redis_datastore)
                title_entities.append(title_entity.redis_key)
        return title_entities
        
    def __ingest__(self):
        "Helper function extracts info from MODS and ingests into RLSP"
        if self.mods_xml is None:
            raise MODSIngesterError("Ingest requires valid MODS XML")
        self.contributors = []
        self.creators = []
        self.instances = []
        work = dict()
        self.__extract_persons__()
        if self.creators is not None:
            work['rda:isCreatedBy'] = set([creator.redis_key
                                           for creator in self.creators])
            work['associatedAgents'] = work['rda:isCreatedBy']
        if self.contributors is not None:
            work['rda:contributor'] = [contributor.redis_key
                                       for contributor in self.contributors]
            if work.has_key('associatedAgents'):
                for redis_key in work['rda:contributor']:
                    work['associatedAgents'].add(redis_key)
            else:
                work['associatedAgents'] = set(work['rda:contributor'])
                
        try:
            title_entities = self.__extract_title__()
            if len(title_entities) == 1:
                work['title'] = title_entities[0]
            else:
                work['title'] = ' '.join(title_entities)
        except ValueError:
            return
        self.__classify_work_class__()
        classifier = self.classifier(entity_info=work,
                                     redis_datastore=self.redis_datastore,
                                     work_class=self.work_class)
        classifier.classify()
        if classifier.creative_work is not None:
            classifier.creative_work.save()
            work_key = classifier.creative_work.redis_key
            # Adds work_key to title entity relatedResources set
            self.redis_datastore.sadd(
                "{0}:relatedResources".format(
                    classifier.creative_work.title),
                work_key)
            for creator_key in work['rda:isCreatedBy']:
                self.redis_datastore.sadd(
                    '{0}:resourceRole:aut'.format(creator_key),
                    work_key)
            self.__create_instances__(work_key)
            for instance_key in self.instances:
                self.redis_datastore.sadd(
                    "{0}:hasInstance".format(work_key),
                    instance_key)
                # 
            
        

    def ingest_file(self, mods_filepath):
        """Method ingests a MODS XML file into RLSP

        Parameters:
        mods_filepath -- File and path to MODS XML
        """
        mods_file = open(mods_filepath, 'rb')
        self.mods_xml = etree.XML(mods_file.read())
        mods_file.close()
        self.__ingest__()

    def ingest_url(self, url):
        """Method ingests a MODS XML URL into RLSP

        Parameters:
        url -- URL to MODS XML
        """
        self.mods_xml = etree.XML(urllib2.urlopen(url).read())
        self.__ingest__()
