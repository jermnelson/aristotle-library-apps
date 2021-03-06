"""
 Tests ingests Project Gutenberg RDF records into BIBFRAME Datastore
"""
__author__ = "Jeremy Nelson"
import datetime
import logging
import os

from lxml import etree

from bibframe.models import Instance, Person, Work, TitleEntity
from bibframe.models import Holding, SoftwareOrMultimedia
from bibframe.ingesters.Ingester import Ingester
from bibframe.ingesters.marc21_maps import LC_CALLNUMBER_MAP
from bibframe.classifiers import simple_fuzzy

from organization_authority.redis_helpers import get_or_add_organization
from person_authority.redis_helpers import get_or_generate_person
from title_search.redis_helpers import index_title



from rdflib import RDF, RDFS
from rdflib import Namespace

from title_search.redis_helpers import index_title, search_title

DCAM = Namespace("http://purl.org/dc/dcam/")
DCTERMS = Namespace("http://purl.org/dc/terms/")
PGTERMS = Namespace("http://www.gutenberg.org/2009/pgterms/")

class ProjectGutenbergIngester(Ingester):
    """
    Class takes a BIBFRAME Annotation, Authority, Creative Work, Instance,
    and Annotation datastores along with a location and ingests the RDF
    record into the Datastore.

    >>> import redis
    >>> local_redis = redis.StrictRedis()
    >>> ingester = ProjectGutenbergIngester(redis_datastore=local_redis)
    >>> ingester.ingest('C:\\ProjectGutenberg\epub\pg01.rdf')
    """                              
                                            

    def __init__(self, **kwargs):
        super(ProjectGutenbergIngester, self).__init__(**kwargs)
        self.classifier = kwargs.get('classifier',
                                     simple_fuzzy.WorkClassifier)
        if self.redis_datastore is not None:
            entity_info = {'label': 'Project Gutenberg',
                           'url': 'http://www.gutenberg.org/'}
            self.project_gutenberg = get_or_add_organization(
                entity_info,
                redis_datastore=self.redis_datastore)
        else:
            self.project_gutenberg = None
                                     

    def __create_instances__(self, rdf_xml, work_key):
        """
        Helper function creates BIBFRAME Instances for the work_key
        based on the RDF and returns the BIBFRAME Redis key of the
        Instances. Currently only creates distinct Instances for 
        html and text. All other formats are ignored but could be
        added later.

        :param rdf_xml: RDF XML
        :param work_key: Redis Work Key
        """
        instances = []
        all_files = rdf_xml.findall('{{{0}}}file'.format(PGTERMS))
        new_holding = Holding(redis_datastore=self.redis_datastore)
        for row in all_files:
            file_format = row.find("{{{0}}}format".format(DCTERMS))
            instance_info = {'instanceOf': work_key,
                             'url':row.attrib['{{{0}}}about'.format(RDF)]}
            new_instance = None
            format_value = file_format.find(
                              "{{{0}}}Description/{{{0}}}value".format(RDF))
            if format_value.text == 'text/html':
                instance_info['rda:carrierTypeManifestation'] = 'online resource'
                new_instance = Instance(redis_datastore=self.redis_datastore)
            if format_value.text == 'text/plain; charset=us-ascii':
                instance_info['rda:carrierTypeManifestation'] = 'online resource'
                new_instance = Instance(redis_datastore=self.redis_datastore)
            if new_instance is not None:
                for key, value in instance_info.iteritems():
                    setattr(new_instance, key, value)
                new_instance.save()
                holding = Holding(redis_datastore=self.redis_datastore,
                                  **{'hasInstance': new_instance.redis_key})
                setattr(holding,
                        'schema:contentLocation',
                        self.project_gutenberg.redis_key)
                holding.save()
                self.redis_datastore.sadd(
                    '{0}:hasAnnotation'.format(new_instance.redis_key),
                    holding.redis_key)
                instances.append(new_instance.redis_key)
        return instances
           

    def __extract_creators__(self, rdf_xml):
        """
        Helper function extracts all agents from RDF and returns
        the BIBFRAME Redis keys of the creators

        :param rdf_xml: RDF XML
        """
        creators = []
        agents = rdf_xml.findall("{{{0}}}agent".format(PGTERMS))
        for agent in agents:
            person = {'identifiers': {'pg': agent.attrib['{{{0}}}about'.format(RDF)]}}
            for element in agent.getchildren():
                if element.tag == '{{{0}}}name'.format(PGTERMS):
                    person['rda:preferredNameForThePerson'] = element.text
                    all_names = [name.strip() for name in element.text.split(",")]
                    person['schema:familyName'] = all_names.pop(0)
                    if len(all_names) > 0:
                        remaining_names = ' '.join(all_names)
                        person['schema:givenName'] = [name.strip() for name in remaining_names.split(' ')][0]
                if element.tag == '{{{0}}}birthdate'.format(PGTERMS):
                    person['rda:dateOfBirth'] = element.text
                if element.tag == '{{{0}}}deathdate'.format(PGTERMS):
                    person['rda:dateOfDeath'] = element.text
            person_result = get_or_generate_person(
                person,
                redis_datastore=self.redis_datastore)
            if type(person_result) == list:
                creators.extend(person_result)
            else:
                creators.append(person_result)
        return set([creator.redis_key for creator in creators])

    def __extract_lcc__(self, rdf_xml):
        """
        Helper function extracts the Library of Congress Classification
        and adds to LOC facet

        Parameter:
        rdf_xml -- RDF XML
        """
        lcc_values = []
        subjects = rdf_xml.findall('{{{0}}}ebook/{{{1}}}subject/{{{2}}}Description'.format(
            PGTERMS,
            DCTERMS,
            RDF))
        for subject in subjects:
            memberOf = subject.find('{{{0}}}memberOf'.format(DCAM))
            if memberOf is not None:
                dc_terms_classification = memberOf.attrib.get(
                    '{{{0}}}resource'.format(RDF))
                if dc_terms_classification == 'http://purl.org/dc/terms/LCC':
                    values = subject.findall("{{{0}}}value".format(RDF))
                    for row in values:
                        lcc_values.append(row.text)
        return lcc_values
                        
        

    def __extract_title__(self, rdf_xml):
        """
        Helper function extracts title information from RDF

        :param rdf_xml: RDF XML
        """
        ebook = rdf_xml.find('{{{0}}}ebook'.format(PGTERMS))
        dc_title = ebook.find('{{{0}}}title'.format(DCTERMS))
        if dc_title is not None:
            title_entity = TitleEntity(redis_datastore=self.redis_datastore,
                                       label=dc_title.text,
                                       titleValue=dc_title.text)
            title_entity.save()
            index_title(title_entity, self.redis_datastore)
            return title_entity.redis_key
        else:
            raise ValueError("Title not found")


    def ingest(self, filepath):
        """
        Method takes a filepath to an RDF xml file from Project Gutenberg and
        attempts to ingest into a BIBFRAME datastore and returns a Creative
        Work Redis key

        :param filepath: Filepath to RDF XML
        """
        work = {}
        if os.path.exists(filepath) is True:
            rdf_xml = etree.XML(open(filepath, 'rb').read())
        else:
            raise IOError("{0} not found".format(filepath))
        work['rda:isCreatedBy'] = self.__extract_creators__(rdf_xml)
        work['associatedAgents'] = work['rda:isCreatedBy']
        lcc_values = self.__extract_lcc__(rdf_xml)
        try:
            work['title'] = self.__extract_title__(rdf_xml)
        except ValueError, e:
            return
        classifier = self.classifier(redis_datastore=self.redis_datastore,
                                     entity_info=work,
                                     work_class=SoftwareOrMultimedia)
        classifier.classify()
        if classifier.creative_work is not None:
            classifier.creative_work.save()
            work_key = classifier.creative_work.redis_key
            for creator_key in work['rda:isCreatedBy']:
                self.redis_datastore.sadd(
                    '{0}:resourceRole:aut'.format(creator_key),
                    work_key)
            # Adds LCC Facet annotations to datastore
            for lcc in lcc_values:
                facet_key = "bf:Annotation:Facet:LOCFirstLetter:{0}".format(
                lcc)
                self.redis_datastore.sadd(facet_key,
                                          work_key)
                self.redis_datastore.sadd(
                    "{0}:hasAnnotation".format(work_key),
                    facet_key)
                self.redis_datastore.hset(
                    "bf:Annotation:Facet:LOCFirstLetters",
                    lcc,
                    LC_CALLNUMBER_MAP.get(lcc))
                self.redis_datastore.zadd(
                    "bf:Annotation:Facet:LOCFirstLetters:sort",
                    float(self.redis_datastore.scard(facet_key)),
                    facet_key)
            # Adds work_key to title entity relatedResources set
            self.redis_datastore.sadd(
                "{0}:relatedResources".format(
                    classifier.creative_work.title),
                work_key)
            instances = self.__create_instances__(rdf_xml, work_key)
            for instance_key in instances:
                self.redis_datastore.sadd('{0}:hasInstance'.format(work_key),
                                           instance_key)
                
            title_key = self.redis_datastore.hget(work_key,
                                                  'title')
            self.redis_datastore.sadd('{0}:relatedResource'.format(title_key),
                                      work_key)
            
