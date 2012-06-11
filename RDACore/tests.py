"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import redis
from django.test import TestCase
import pymarc

test_ds = redis.StrictRedis(db=REDIS_TEST_DB)

class CreateRDACoreEntityFromMARCTest(TestCase):

    def setUp(self):
        self.test_rec = pymarc.Record()
        self.root_key = "rdaCore:{0}".format(test_ds.incr("global:rdaCore"))
        self.entity_generator = CreateRDACoreEntityFromMARC(record=self.test_erc,
                                                            redis_server=test_ds,
                                                            root_redis_key=self.root_key,
                                                            entity='Generic')

    def test_init(self):
        self.assertEquals(self.entity_generator.entity_key,
                          "{0}:Generic:1".format(self.root_key))
                                               

    def test_add_attribute(self):
        self.entity_generator.__add_attribute__("name",["testing",])
        self.assert_(test_ds.hexists(self.entity_generator.entity_key,
                                     "name"))
        self.assertEquals(test_ds.hget(self.entity_generator.entity_key,
                                       "name"),
                          "testing")
        self.entity_generator.__add_attribute__("name",["testing two",])
        # Hash value for attribute should now be deleted
        self.assert_(not test_db.hexists(self.entity_generator.entity_key,
                                         "name"))
        # Set should now exist for entity
        entity_attribute_set_key = "{0}:{1}".format(self.entity_key,"name")
        self.assert_(test_db.exists(entity_attribute_set_key))
        
        

    def tearDown(self):
        test_ds.flushdb()
        
        



    
        
