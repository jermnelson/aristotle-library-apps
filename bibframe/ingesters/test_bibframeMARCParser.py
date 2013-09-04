__author__ = "Jeremy Nelson"

import pymarc
from aristotle.settings import PROJECT_HOME, TEST_REDIS
from unittest import TestCase


import bibframeMARCParser as parser

class conditional_MARC21Test(TestCase):

    def setUp(self):
        self.rule1 = {
        "conditional": "if marc:0247_2 is 'isbn'", 
        "map": "marc:0247_a"}
        self.rule2 = {
        "conditional": "if marc:85600u.count('doi') > 0", 
        "map": "marc:85600u"}
        self.marc_record = pymarc.Record()
        self.marc_record.add_field(pymarc.Field(
            tag='024',
            indicators=['7', ' '],
            subfields=['a', '3813501159', '2', 'isbn']))
        self.marc_record.add_field(pymarc.Field(
            tag='856',
            indicators=['0', '0'],
            subfields=['u', 'http://doi.example.com/']))

    def test_rule_one(self):
        result = parser.conditional_MARC21(
            self.marc_record,
            self.rule1)
        self.assertEquals(result,
                          ['3813501159'])

    def test_rule_two(self):
        result = parser.conditional_MARC21(
            self.marc_record,
            self.rule2)
        self.assertEquals(result,
                          ['http://doi.example.com/'])

    def tearDown(self):
        TEST_REDIS.flushdb()

class MARC21toBIBFRAMERegexTest(TestCase):

    def setUp(self):
        pass

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

class MARC21toBIBFRAMEBasicConditionalRETest(TestCase):

    def setUp(self):
        self.result = parser.BASIC_CONDITIONAL_RE.search(
            "if marc:0247_2 is 'doi'").groupdict()

    def test_re_marc_value(self):
        self.assertEquals(self.result.get('marc'),
                          'marc:0247_2')

    def test_re_operator(self):
        self.assertEquals(self.result.get('operator'),
                          'is')

    def test_re_string(self):
        self.assertEquals(self.result.get('string'),
                          'doi')

    def tearDown(self):
        TEST_REDIS.flushdb()


class MARC21toBIBFRAMEMethodConditionalRETest(TestCase):

    def setUp(self):
        self.result = parser.METHOD_CONDITIONAL_RE.search(
            "if marc:85602u.count('doi') > 0").groupdict()

    def test_re_marc_value(self):
        self.assertEquals(self.result.get('marc'),
                          'marc:85602u')

    def test_re_method(self):
        self.assertEquals(self.result.get('method'),
                          'count')

    def test_re_operator(self):
        self.assertEquals(self.result.get('operator'),
                          '>')

    def test_re_param(self):
        self.assertEquals(self.result.get('param'),
                          'doi')

    def test_re_string(self):
        self.assertEquals(self.result.get('string'),
                          '0')


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
        
