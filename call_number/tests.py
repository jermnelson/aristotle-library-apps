"""
 mod:`tests` Unit tests for Call Number Application
"""
__author__ = "Jeremy Nelson"
from django.test import TestCase
from django.test.client import Client
from redis_helpers import lccn_normalize

web_client = Client()

class WidgetTest(TestCase):

    def test_view(self):
        widget_response = web_client.get('/apps/call_number/widget')
        self.assertEquals(widget_response.status_code,
                          200)

class LCCNNormalizeTest(TestCase):

    def test_normalization(self):
        self.assertEquals('A 0001',
                          lccn_normalize('A1'))
        self.assertEquals('B 002230',
                          lccn_normalize('B22.3'))
        self.assertEquals('C 000100D110',
                          lccn_normalize('C1.D11'))
        self.assertEquals('D 001540D220 000 000 1990',
                          lccn_normalize('D15.4 .D22 1990'))
                          
        
    
        
