"""
This file demonstrates writing tests using the unittest module.


"""
__author__ = "Jeremy Nelson"

from aristotle.settings import TEST_REDIS
from django.test import TestCase
from keyword_search import whoosh_helpers

class SimpleSearchTest(TestCase):

    
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
