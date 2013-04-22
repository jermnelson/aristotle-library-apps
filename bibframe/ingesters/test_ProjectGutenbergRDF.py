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
        self.ingester = ProjectGutenbergIngester(annotation_ds=TEST_REDIS,
                                                 authority_ds=TEST_REDIS,
                                                 creative_work_ds=TEST_REDIS,
                                                 instance_ds=TEST_REDIS)
        self.ingester.ingest(os.path.join(PROJECT_HOME,
                                             'bibframe',
                                             'fixures',
                                             'pg',
                                             'pg33.rdf'))

        

    def test_init(self):
        self.assert_(self.ingester)

    def test_extract_creator(self):
        self.assertEquals(TEST_REDIS.hget('bibframe:Person:1',
                                          'rda:dateOfBirth'),
                          '1804')
        self.assertEquals(TEST_REDIS.hget('bibframe:Person:1',
                                          'rda:dateOfDeath'),
                          '1864')

    def test_extract_title(self):
        self.assertEquals(TEST_REDIS.hget('bibframe:Work:1:title',
                                          'rda:preferredTitleForTheWork'),
                          'The Scarlet Letter')
        
                                          
        

    def tearDown(self):
        TEST_REDIS.flushdb()

        
                
