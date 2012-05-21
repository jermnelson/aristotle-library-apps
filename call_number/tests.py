"""
 mod:`tests` Unit tests for Call Number Application
"""
__author__ = "Jeremy Nelson"
from django.test import TestCase
from django.test.client import Client
from redis_helpers import lccn_normalize

web_client = Client()

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

class WidgetTest(TestCase):

    def test_view(self):
        widget_response = web_client.get('/call_number/widget')
        self.assertEquals(widget_response.status_code,
                          200)

class LCCNNormalizeTest(TestCase):

    def test_normalization(self):
        self.assertEquals('A 0001',
                          lccn_normalize('A1'))
        self.assertEquals('B 002230',
                          lccn_normalize('B22.3'))
        
    
        
