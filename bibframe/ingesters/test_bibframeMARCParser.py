__author__ = "Jeremy Nelson"

import pymarc
from aristotle.settings import PROJECT_HOME, TEST_REDIS
from unittest import TestCase


import bibframeMARCParser as parser

class MARC21toBIBFRAMERegexTest(TestCase):

    def setUp(self):
        pass

    def test_init(self):
        self.assert_(1)

    def test_marc_field_re(self):
        "Tests MARC_FLD_RE in bibframeMARCParser parser class"
        first_result = parser.MARC_FLD_RE.search('marc:0411_b').groupdict()
        self.assertEquals(first_result.get('tag'),
                          '041')
        self.assertEquals(first_result.get('ind1'),
                          '1')
        self.assertEquals(first_result.get('ind2'),
                          '_')
        self.assertEquals(first_result.get('subfield'),
                          'b')

    def test_marc_field_re2(self):
        result = parser.MARC_FLD_RE.search('marc:080__a').groupdict()
        self.assertEquals(result.get('tag'),
                          '080')
        self.assertEquals(result.get('ind1'),
                          '_')
        self.assertEquals(result.get('ind2'),
                          '_')
        self.assertEquals(result.get('subfield'),
                          'a')

    def tearDown(self):
        TEST_REDIS.flushdb()

class parse_MARC21Test(TestCase):

    def setUp(self):
        self.marc_record = pymarc.Record()
        self.marc_record.add_field(pymarc.Field(
            tag='041',
            indicators=['1', ' '],
            subfields=['a', 'esp', 'b', 'eng']))

    def test_041(self):
        self.assertEquals(parser.parse_MARC21(self.marc_record,
                                              'marc:0411_b'),
                          ['eng'])

    

    def tearDown(self):
        TEST_REDIS.flushdb()
        
