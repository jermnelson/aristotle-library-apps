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
from bibframe.models import Person, Audio, Book, Cartography, MixedMaterial  
from bibframe.models import MovingImage, MusicalAudio, NonmusicalAudio, NotatedMusic 
from bibframe.models import SoftwareOrMultimedia, StillImage, TitleEntity
from bibframe.models import ThreeDimensionalObject
from person_authority.redis_helpers import get_or_generate_person
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
        self.classifier = kwargs.get('classifier',
                                     simple_fuzzy.WorkClassifier)
        self.work_class = kwargs.get('work_class',
                                     Work)
        self.creators = []
        self.mods_xml = None

    def __classify_work_class__(self):
        "Helper function classifies a work based on typeOfResource"
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
        instances = []
        # Create an instance for each originInfo element in MODS
        origin_infos = self.mods_xml.findall('{{{0}}}originInfo'.format(
            MODS_NS))
        form = self.mods_xml.find(
            '{{{0}}}physicalDescription/{{{0}}}form'.format(MODS_NS))
        for element in origin_infos:
            instance_of = {'instanceOf': work_key}
            if form.attrib.get('type', None) == 'carrier':
                if form.attrib.get('authority', None) == 'rdacarrier':
                    instance_of['rda:carrierTypeManifestation'] = form.text
            extent = element.find('{{{0}}}extent'.format(MODS_NS))
            if extent is not None:
                if extent.text is not None:
                    instance_of['extent'] = extent.text
            new_instance = Instance(redis_datastore=self.redis_datastore,
                                    **instance_of)
            new_instance.save()
            instances.append(new_instance.redis_key)
        return instances


    def __extract_creator__(self, name_parts):
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
            name_value = row.text.strip().title()
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
                        person[key] = value
        return person
            
            
    def __extract_creators__(self):
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
            if role.text == 'creator':
                person = self.__extract_creator__(name_parts)
            if person is not None:
                self.creators.append(get_or_generate_person(person,
                                                            self.redis_datastore))

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
                # equalvant to MARC 245 $b
                subtitle = titleInfo.find('{{{0}}}subTitle'.format(MODS_NS))
                if subtitle is not None and len(subtitle.text) > 0:
                    output['subtitle'] = subtitle.text
                # equalivant to MARC 245 $p
                partTitle = titleInfo.find('{{{0}}}partName'.format(MODS_NS))
                if partTitle is not None and len(partTitle.text) > 0:
                    output['partTitle'] = partTitle.text
            if len(output) > 0:
                title_entity = TitleEntity(redis_datastore=self.redis_datastore,
                                           **output)
                title_entity.save()
                title_entities.append(title_entity.redis_key)
        return title_entities
        
    def __ingest__(self):
        "Helper function extracts info from MODS and ingests into RLSP"
        if self.mods_xml is None:
            raise MODSIngesterError("Ingest requires valid MODS XML")
        work = dict()
        self.__extract_creators__()
        if self.creators is not None:
            work['rda:isCreatedBy'] = [creator.redis_key
                                       for creator in self.creators]
            work['associatedAgents'] = work['rda:isCreatedBy']
        try:
            title_entities = self.__extract_title__()
            if len(title_entities) == 1:
                work['title'] = title_entities[0]
            else:
                work['title'] = ' '.join(title_entities)
        except ValueError:
            return
        work_class = self.__classify_work_class__()
        classifier = self.classifier(entity_info=work,
                                     redis_datastore=self.redis_datastore)
        classifier.classify()
        if classifier.creative_work is not None:
            classifier.creative_work.save()
            work_key = classifier.creative_work.redis_key
            for creator_key in work['rda:isCreatedBy']:
                self.redis_datastore.sadd(
                    '{0}:resourceRole:aut'.format(creator_key),
                    work_key)
            instances = self.__create_instances__(work_key)
            for instance_key in instances:
                self.redis_datastore.sadd(
                    "{0}:hasInstance".format(work_key),
                    instance_key)
            
        

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
