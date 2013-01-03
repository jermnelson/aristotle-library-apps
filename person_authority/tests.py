"""
 :mod:`tests` Unit Tests for Person Authority App
"""
import os
from django.test import TestCase
from redis_helpers import *
from aristotle.settings import PROJECT_HOME,TEST_REDIS

authority_redis = TEST_REDIS


class AddPersonTest(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        authority_redis.flushdb()

class GetOrGeneratePersonTest(TestCase):

    def setUp(self):
        attributes = {"rda:preferredNameForThePerson":"Wallace, David Foster",
                      "rda:dateOfBirth":1960,
                      "rda:dateOfDeath":2008}
        self.person = get_or_generate_person(attributes,
                                             authority_redis)
    
    def test_get_or_generate_person(self):
        """
        Tests redis_helpers.get_or_generate_person 
        """
        self.assert_(self.person.redis_key)

    def test_duplicates(self):
        """
        Tests duplicates based on Pride and Prejudices multiple
        MARC21 record examples
        """
        austen_attrs = {"rda:preferredNameForThePerson":"Austen, Jane",
                        "rda:dateOfBirth":1775,
                        "rda:dateOfDeath":1817}
        jane_austen = get_or_generate_person(austen_attrs,authority_redis)
        test_person = get_or_generate_person(austen_attrs,authority_redis)
        self.assertEquals(jane_austen.redis_key,
                          test_person.redis_key)                          
        
        
        
        
        

    def tearDown(self):
        authority_redis.flushdb()
