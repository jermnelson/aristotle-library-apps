# -*- coding: cp1252 -*-
"Unit tests for marc_helpers module"
__author__ = "Jeremy Nelson"

import pymarc

from aristotle.settings import TEST_REDIS
from unittest import TestCase
from marc_batch.marc_helpers import *

class TestCleanUnicodeFunction(TestCase):

    def setUp(self):
        self.marc_record = pymarc.Record(to_unicode=True)
        self.marc_record.add_field(
            pymarc.Field(
                tag='245',
                indicators=['0', '0'],
                subfields=['a', 'Cortazar',
                           'b', 'Cartas de Mama /',
                           'c', u"Radiotelevisio´n Espan~ola."]))
            

    def test_clean_unicode(self):
        cleaned_record = clean_unicode(self.marc_record)
        self.assertEquals(cleaned_record['245']['c'],
                          u"Radiotelevisión Española.")
        
        

    def tearDown(self):
        TEST_REDIS.flushdb()
