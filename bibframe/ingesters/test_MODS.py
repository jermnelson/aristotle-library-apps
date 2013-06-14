"""
 Unit tests for the MODS Ingester module. 
"""
__author__ = "Jeremy Nelson"

import os
import unittest
from bibframe.ingesters.MODS import *
from aristotle.settings import TEST_REDIS, PROJECT_HOME
from rdflib import Namespace

MODS_NS = Namespace('http://www.loc.gov/mods/v3')

class TestMODSforOralHistoryIngester(unittest.TestCase):

    def setUp(self):
        self.ingester = MODSIngester(redis_datastore=TEST_REDIS)
        self.ingester.ingest_file(os.path.join(PROJECT_HOME,
                                               'bibframe',
                                               'fixures',
                                               'helen-jackson.xml'))

    def test_init(self):
        self.assert_(self.ingester is not None)

    def test_ingest_error(self):
        new_ingester = MODSIngester(annotation_ds=TEST_REDIS,
                                     authority_ds=TEST_REDIS,
                                     creative_work_ds=TEST_REDIS,
                                     instance_ds=TEST_REDIS)
        self.assertRaises(MODSIngesterError, new_ingester.__ingest__)

    def test_ingest_podcast(self):
        self.assert_(self.ingester.mods_xml is not None)

    def test_creators(self):
        creator_key = self.ingester.creators[0].redis_key
        self.assert_(creator_key)
        self.assertEquals(TEST_REDIS.hget(creator_key,
                                          'schema:familyName'),
                          'Finley')
        self.assertEquals(TEST_REDIS.hget(creator_key,
                                          'schema:givenName'),
                          'Judith')
        self.assertEquals(TEST_REDIS.hget(creator_key,
                                          'schema:additionalName'),
                          'Reid')
        self.assertEquals(TEST_REDIS.hget(creator_key,
                                          'rda:dateOfBirth'),
                          '1936')
        self.assertEquals(TEST_REDIS.hget(creator_key,
                                          "rda:preferredNameForThePerson"),
                          
                          "Finley, Judith Reid, 1936-")

    def test_title(self):
        title_dict = self.ingester.__extract_title__()
        self.assertEquals(title_dict.get('rda:preferredTitleForTheWork'),
                          'Jackson, Helen')
        

    def tearDown(self):
        TEST_REDIS.flushdb()
        
                                          
        
