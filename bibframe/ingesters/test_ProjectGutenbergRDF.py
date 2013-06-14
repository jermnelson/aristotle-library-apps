"""
 Tests ingests Project Gutenberg RDF records into BIBFRAME Datastore
"""
__author__ = "Jeremy Nelson"
import datetime
import logging
import os
import unittest

from aristotle.settings import TEST_REDIS, PROJECT_HOME
from bibframe.ingesters.ProjectGutenbergRDF import ProjectGutenbergIngester
from lxml import etree
from rdflib import Namespace, RDF, RDFS


DCTERMS = Namespace("http://purl.org/dc/terms/")
PGTERMS = Namespace("http://www.gutenberg.org/2009/pgterms/")

    
class TestProjectGutenbergIngester(unittest.TestCase):

    def setUp(self):
        self.ingester = ProjectGutenbergIngester(redis_datastore=TEST_REDIS)
        self.ingester.ingest(os.path.join(PROJECT_HOME,
                                             'bibframe',
                                             'fixures',
                                             'pg',
                                             'pg33.rdf'))

    def test_init(self):
        self.assert_(self.ingester)

    def test_association_work_creator(self):
        self.assertEquals(TEST_REDIS.hget('bf:SoftwareOrMultimedia:1',
                                          'rda:isCreatedBy'),
                          'bf:Person:1')
        self.assertEquals(TEST_REDIS.smembers(
            'bf:SoftwareOrMultimedia:1:hasInstance'),
                          set(['bibframe:Instance:1',
                               'bibframe:Instance:2']))

    def test_create_instances(self):
        self.assertEquals(TEST_REDIS.hget('bf:Instance:1',
                                          'instanceOf'),
                          'bf:SoftwareOrMultimedia:1')
        self.assertEquals(TEST_REDIS.hget('bibframe:Instance:2',
                                          'instanceOf'),
                          'bf:SoftwareOrMultimedia:1')



    def test_extract_creator(self):
        self.assertEquals(TEST_REDIS.hget('bibframe:Person:1',
                                          'rda:dateOfBirth'),
                          '1804')
        self.assertEquals(TEST_REDIS.hget('bibframe:Person:1',
                                          'rda:dateOfDeath'),
                          '1864')
        self.assertEquals(TEST_REDIS.hget('bibframe:Person:1',
                                          'rda:preferredNameForThePerson'),
                          "Hawthorne, Nathaniel")
        self.assertEquals(TEST_REDIS.hget('bibframe:Person:1',
                                          'schema:givenName'),
                          "Nathaniel")
        self.assertEquals(TEST_REDIS.hget('bibframe:Person:1',
                                          'schema:familyName'),
                          "Hawthorne")

    def test_extract_title(self):
        self.assertEquals(TEST_REDIS.hget('bibframe:Work:1:title',
                                          'rda:preferredTitleForTheWork'),
                          'The Scarlet Letter')

    def test_multiple_creators(self):
       ## TEST_REDIS.flushdb()
        self.ingester.ingest(os.path.join(PROJECT_HOME,
                                             'bibframe',
                                             'fixures',
                                             'pg',
                                             'pg1682.rdf'))
        self.assertEquals(TEST_REDIS.hget('bibframe:Person:1',
                                          'schema:familyName'),
                          'Plato')
        self.assertEquals(TEST_REDIS.hget('bibframe:Person:2',
                                          'rda:preferredNameForThePerson'),
                          'Jowett, Benjamin')



    def tearDown(self):
        ## TEST_REDIS.flushdb()
        pass

                
