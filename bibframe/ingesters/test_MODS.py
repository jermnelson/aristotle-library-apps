"""
 Unit tests for the MODS Ingester module. 
"""
__author__ = "Jeremy Nelson"

import os
import unittest
from bibframe.models import MixedMaterial, MusicalAudio
from bibframe.ingesters.MODS import *
from aristotle.settings import TEST_REDIS, PROJECT_HOME
from lxml import etree
from rdflib import Namespace


MODS_NS = Namespace('http://www.loc.gov/mods/v3')

MODS_NSMAP = {"mods": "http://www.loc.gov/mods/v3",
              "xlink": "http://www.w3.org/1999/xlink",
              "xsi": "http://www.w3.org/2001/XMLSchema-instance"}


class TestGeneralMODSIngester(unittest.TestCase):

    def setUp(self):
        pass

    def test_classify_musical_audio(self):
        mods_xml = etree.Element("{{{0}}}mods".format(MODS_NS),
                                 nsmap=MODS_NSMAP)
        ingester = MODSIngester(redis_datastore=TEST_REDIS)
        type_of_resource = etree.SubElement(
            mods_xml,
            "{{{0}}}typeOfResource".format(MODS_NS))
        type_of_resource.text = "sound recording-musical"
        ingester.mods_xml = mods_xml
        ingester.__classify_work_class__()
        self.assertEquals(ingester.work_class, MusicalAudio)

    def test_classify_mixed_material(self):
        mods_xml = etree.Element("{{{0}}}mods".format(MODS_NS),
                                 nsmap=MODS_NSMAP)
        ingester = MODSIngester(redis_datastore=TEST_REDIS)
        type_of_resource = etree.SubElement(
            mods_xml,
            "{{{0}}}typeOfResource".format(MODS_NS))
        type_of_resource.text = "mixed material"
        ingester.mods_xml = mods_xml
        ingester.__classify_work_class__()
        self.assertEquals(ingester.work_class, MixedMaterial)

    def tearDown(self):
        pass
                          
        

class TestMODSforOralHistoryIngester(unittest.TestCase):

    def setUp(self):
        self.ingester = MODSIngester(redis_datastore=TEST_REDIS)
        self.ingester.ingest_file(os.path.join(PROJECT_HOME,
                                               'bibframe',
                                               'fixures',
                                               'helen-jackson.xml'))

    def test_init(self):
        self.assert_(self.ingester is not None)

    def test_work_class(self):
        self.assertEquals(self.ingester.work_class,
                          MixedMaterial)

    def test_ingest_error(self):
        new_ingester = MODSIngester(redis_datastore=TEST_REDIS)
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
        title_list = self.ingester.__extract_title__()
        self.assertEquals(TEST_REDIS.hget(title_list[0],
                                          'titleValue'),
                          'Jackson, Helen')
        

    def tearDown(self):
        TEST_REDIS.flushdb()
##        pass
        
                                          
        
