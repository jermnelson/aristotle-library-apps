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

        self.austen_attrs = {"rda:preferredNameForThePerson":"Austen, Jane",
                             "rda:dateOfBirth":1775,
                             "rda:dateOfDeath":1817}
        self.jane_austen = get_or_generate_person(self.austen_attrs,authority_redis)
 

    
    def test_get_or_generate_person(self):
        """
        Tests redis_helpers.get_or_generate_person 
        """
        self.assert_(self.person.redis_key)

    def test_duplicate1(self):
        """
        Tests duplicates based on Pride and Prejudices multiple
        MARC21 record examples
        """
        test_person = get_or_generate_person(self.austen_attrs,authority_redis)
        self.assertEquals(self.jane_austen.redis_key,
                          test_person.redis_key) 


    def test_not_duplicate(self):
        test_person = get_or_generate_person({"rda:preferredNameForThePerson":"Austen, Jane",
                                              "rda:dateOfBirth":1990},
                                             authority_redis)
        self.assertNotEquals(self.jane_austen.redis_key,
                             test_person.redis_key)


    def test_duplicate2(self):
        test_person = get_or_generate_person({"rda:preferredNameForThePerson":"Austen, Jane",
                                              "rda:dateOfBirth":1775},
                                             authority_redis)
        self.assertEquals(test_person.redis_key,
                          self.jane_austen.redis_key)        
       


    def tearDown(self):
        authority_redis.flushdb()
