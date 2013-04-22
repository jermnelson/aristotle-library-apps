"""
 Tests ingests Project Gutenberg RDF records into BIBFRAME Datastore
"""
__author__ = "Jeremy Nelson"
import datetime
import logging
import os

from lxml import etree

from bibframe.models import Instance, Person, Work
from bibframe.ingesters.Ingester import Ingester
from bibframe.classifiers import simple_fuzzy

from person_authority.redis_helpers import get_or_generate_person

from rdflib import RDF, RDFS
from rdflib import Namespace

from title_search.redis_helpers import search_title

DCTERMS = Namespace("http://purl.org/dc/terms/")
PGTERMS = Namespace("http://www.gutenberg.org/2009/pgterms/")

class ProjectGutenbergIngester(Ingester):
    """
    Class takes a BIBFRAME Annotation, Authority, Creative Work, Instance,
    and Annotation datastores along with a location and ingests the RDF
    record into the Datastore.

    >>> import redis
    >>> local_redis = redis.StrictRedis()
    >>> ingester = ProjectGutenbergIngester(annotation_ds=local_redis,
                                            authority_ds=local_redis,
                                            creative_work_ds=local_redis,
                                            instance_ds=local_redis)
    >>> ingester.ingest('C:\\ProjectGutenberg\epub\pg01.rdf')
    """                              
                                            

    def __init__(self, **kwargs):
        super(ProjectGutenbergIngester, self).__init__(**kwargs)
        self.classifier = kwargs.get('classifier',
                                     simple_fuzzy.WorkClassifier)
                                     

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
                if element.tag == '{{{0}}}birthdate'.format(PGTERMS):
                    person['rda:dateOfBirth'] = element.text
                if element.tag == '{{{0}}}deathdate'.format(PGTERMS):
                    person['rda:dateOfDeath'] = element.text
            creators.append(get_or_generate_person(person,
                                                   self.authority_ds))
        return creators

    def __extract_title__(self, rdf_xml):
        """
        Helper function extracts title information from RDF

        :param rdf_xml: RDF XML
        """
        ebook = rdf_xml.find('{{{0}}}ebook'.format(PGTERMS))
        dc_title = ebook.find('{{{0}}}title'.format(DCTERMS))
        if dc_title is not None:
            return {'rda:preferredTitleForTheWork': dc_title.text}
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
        work['title'] = self.__extract_title__(rdf_xml)
        classifier = self.classifier(creative_work_ds=self.creative_work_ds,
                                     entity_info=work)
        classifier.classify()
        if classifier.creative_work is not None:
            classifier.creative_work.save()
        
        
        
        
                
