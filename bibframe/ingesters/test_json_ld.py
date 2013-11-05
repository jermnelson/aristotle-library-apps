"""Unit tests for JSON Linked Data Ingester module"""

__author__ = "Jeremy Nelson"

import json
import sys
import os
import unittest

from aristotle.settings import TEST_REDIS
import bibframe.models as models
from bibframe.ingesters.json_ld import *

TEST_WORK = {'@context': {'bf': 'http://bibframe.org/vocab/',
              'prov': 'http://www.w3.org/ns/prov#',
              'rda': 'http://rdvocab.info',
              'schema': 'http://schema.org/'},
             '@type': 'bf:Manuscript',
 'bf:hasInstance': [{'@type': 'bf:Instance',
                    'prov:Generation': {'prov:atTime': '2013-07-31T21:38:17.191000',
                                        'prov:wasGeneratedBy': 'http://id.loc.gov/authorities/names/n84168445'},
                    'rda:carrierTypeManifestation': 'online resource',
                    'schema:contentUrl': '/pdf/Harrington_mf5_r6.pdf'}],
 'bf:subject': [{'@type': 'bf:Topic',
                 'bf:hasAuthority': 'http://id.loc.gov/authorities/names/no2008011986',
                 'bf:identifier': 'http://id.loc.gov/authorities/subjects/sh85072494',
                 'bf:label': u'Kiowa Indians',
                 'prov:Generation': {'prov:atTime': '2013-07-31T21:38:17.191000',
                                     'prov:wasGeneratedBy': 'http://id.loc.gov/authorities/names/n84168445'}}],
 'bf:title': {'@type': 'bf:Title',
              'bf:titleValue': 'John P. Harrington Papers 1907-1959 (some earlier) Microfilm 5, Reel 6 Dictionary'},
 'prov:Generation': {'prov:atTime': '2013-07-31T21:38:17.191000',
                     'prov:wasGeneratedBy': 'http://id.loc.gov/authorities/names/n84168445'},
 'rda:dateOfPublicationManifestation': '1986'}

class TestJSONLinkedDataIngester(unittest.TestCase):

    def setUp(self):
        pass

    def test_init_(self):
        ingester = JSONLinkedDataIngester(redis_datastore=TEST_REDIS)
        self.assert_(ingester.linked_data is None)

    def test_extract_authority_lcsh(self):
        ingester = JSONLinkedDataIngester(redis_datastore=TEST_REDIS)
        authority_key = ingester.__extract_authority_lcsh__(
            'http://id.loc.gov/authorities/names/no2008011986')
        self.assertEquals(authority_key,
                          'bf:Organization:1')
        self.assertEquals(TEST_REDIS.hget(authority_key,
                                          'label'),
                          'Library of Congress. Working Group on the Future of Bibliographic Control')
        

    def test_extract_instances(self):
        ingester = JSONLinkedDataIngester(redis_datastore=TEST_REDIS)
        instances = [{'@type': 'bf:Instance',
                      'rda:carrierTypeManifestation': 'online resource',
                      'schema:contentUrl': '/pdf/Harrington_mf5_r6.pdf'},
                     {'@type': 'bf:Instance',
                      'rda:carrierTypeManifestation': 'microfilm'}]
        ingester.__extract_instances__(instances)
        self.assertEquals(
            TEST_REDIS.hget('bf:Instance:1',
                            'rda:carrierTypeManifestation'),
            'online resource')
        self.assertEquals(
            TEST_REDIS.hget('bf:Instance:1',
                            'schema:contentUrl'),
            '/pdf/Harrington_mf5_r6.pdf')
        self.assertEquals(
            TEST_REDIS.hget('bf:Instance:2',
                            'rda:carrierTypeManifestation'),
            'microfilm')
  

    def test_extract_title_entity(self):
        ingester = JSONLinkedDataIngester(redis_datastore=TEST_REDIS)
        self.assertEquals(ingester.__extract_title_entity__(
            TEST_WORK.get('bf:title')),
            'bf:Title:1')
        self.assertEquals(TEST_WORK.get('bf:title').get('bf:titleValue'),
            TEST_REDIS.hget('bf:Title:1', 'titleValue'))
            

    def test_extract_topics(self):
        wichita_indians_topic = models.Topic(redis_datastore=TEST_REDIS,
                                             label='Wichita Indians')
        wichita_indians_topic.save()
        TEST_REDIS.hset('lcsh-hash',
                        'http://id.loc.gov/authorities/subjects/sh85028785',
                        wichita_indians_topic.redis_key)
        ingester = JSONLinkedDataIngester(redis_datastore=TEST_REDIS)
        topics = [
            {'bf:identifier': 'http://id.loc.gov/authorities/subjects/sh85018617',
             'bf:label': u'Caddo Indians' },
            {'bf:identifier': 'http://id.loc.gov/authorities/subjects/sh85146582',
             'bf:label': u'Wichita Indians'},
            {'bf:identifier': 'http://id.loc.gov/authorities/subjects/sh85028785',
             'bf:label':  u'Comanche Indians'}]
        self.assertEquals(ingester.__extract_topics__(topics),
                          ['bf:Topic:2', 'bf:Topic:3', 'bf:Topic:1'])
                  
    def test_ingest(self):
        ingester = JSONLinkedDataIngester(redis_datastore=TEST_REDIS)
        ingester.linked_data = TEST_WORK
        self.assert_(not TEST_REDIS.exists('bf:Manuscript:1'))
        ingester.__ingest__()
        self.assert_(TEST_REDIS.exists('bf:Manuscript:1'))
        self.assertEquals(
            TEST_REDIS.hget("bf:Manuscript:1",
                            'rda:dateOfPublicationManifestation'),
            '1986')
        self.assertEquals(
            TEST_REDIS.hget('bf:Manuscript:1',
                            'hasInstance'),
            'bf:Instance:1')
        self.assertEquals(
            TEST_REDIS.hget('bf:Manuscript:1',
                            'subject'),
            'bf:Topic:1')
        
        

    def test_ingest_exception(self):
        ingester = JSONLinkedDataIngester(redis_datastore=TEST_REDIS)
        ingester.linked_data = {'@type': 'schema:Book'}
        self.assertRaises(ValueError, ingester.__ingest__)
        ingester.linked_data = {'@type': 'bf:GlobleyGook'}
        self.assertRaises(ValueError, ingester.__ingest__)
        

    def tearDown(self):
        TEST_REDIS.flushdb()
