"""
 :mod:`tests` Unit Tests for Person Authority App
"""

from django.test import TestCase
from redis_helpers import *
from aristotle.settings import TEST_REDIS

authority_redis = TEST_REDIS

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
        

    def tearDown(self):
        authority_redis.flushdb()
