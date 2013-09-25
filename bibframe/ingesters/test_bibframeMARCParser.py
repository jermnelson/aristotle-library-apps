__author__ = "Jeremy Nelson"

import pymarc
from aristotle.settings import PROJECT_HOME, TEST_REDIS
from unittest import TestCase


import bibframeMARCParser as parser

class conditional_MARC21Test(TestCase):

    def setUp(self):
        self.rule1 = {
        "conditional": "if marc:0247_2 is 'isbn'", 
        "map": ["marc:0247_a"]}
        self.rule2 = {
        "conditional": "if marc:85600u.count('doi') > 0", 
        "map": ["marc:85600u"]}
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

    def test_marc_fixed_field_re(self):
        result = parser.MARC_FX_FLD_RE.search('marc:007v01').groupdict()
        self.assertEquals(result.get('tag'),
                          '007')
        self.assertEquals(result.get('position'),
                          '01')
        self.assertEquals(result.get('code'),
                          'v')

    def test_marc_fixed_field_range_re(self):
        result = parser.MARC_FX_FLD_RANGE_RE.search("marc:00818-21").groupdict()
        self.assertEquals(result.get('tag'),
                          '008')
        self.assertEquals(result.get('start'),
                          '18')
        self.assertEquals(result.get('end'),
                          '21')

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

class parse_fixed_fieldTest(TestCase):

    def setUp(self):
        pass

    def test_marc007m04(self):
        field007 = pymarc.Field(
            tag='007',
            data='m   a')
        search = parser.MARC_FX_FLD_RE.search("marc:007m04")
        result = parser.parse_fixed_field(
            field007,
            search.groupdict())
        self.assertEquals(result,
                          ['Standard sound aperture (reduced frame)'])

    def tearDown(self):
        TEST_REDIS.flushdb()

class parse_variable_fieldTest(TestCase):

    def setUp(self):
        pass

    def test_marc02840a(self):
        field028 = pymarc.Field(
            tag='028',
            indicators=['4', '0'],
            subfields = ['a', 'video-3456'])
        search = parser.MARC_FLD_RE.search("marc:02840a")
        re_group = search.groupdict()
        result = parser.parse_variable_field(
            field028,
            re_group)
        self.assertEquals(result,
                          ['video-3456'])

    def tearDown(self):
        TEST_REDIS.flushdb()

class post_processingTest(TestCase):

    def setUp(self):
        self.marc_record = pymarc.Record()
        self.marc_record.add_field(pymarc.Field(
            tag='083',
            indicators=[' ', ' '],
            subfields=['a', '589.0994',
                       'c', '589.10']))
        self.rules = [{
            "conditional": None,
            "map": "marc:083__a"},
                      {
            "conditional": None,
            "map": "marc:083__c"}]
        self.results = []
        for rule in self.rules:
            self.results.extend(
                parser.parse_MARC21(self.marc_record,
                                    rule.get('map')))
        self.directive =  {
            "type": "delimiter",
            "value": "-"}

    def test_concat_post_processing(self):
        value = parser.post_processing(["Title", "2nd", "ed"],
                                       'concat')
        self.assertEquals(value,
                          "Title 2nd ed")
                                       
                                    

    def test_delimiter_post_processing(self):
        value = parser.post_processing(self.results,
                                       self.directive)
        self.assertEquals(value,
                          '589.0994-589.10')
                                       
        
                       
            
            

    def tearDown(self):
        TEST_REDIS.flushdb()



