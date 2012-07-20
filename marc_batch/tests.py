"""
 :mod:`tests` Unit Tests for MARC Batch App functionality 
"""
__author__ = "Jeremy Nelson"
import redis,pymarc,datetime
import json
from django.test import TestCase
from aristotle.settings import REDIS_TEST_DB
from jobs.rdaCore_redis import *


test_ds = redis.StrictRedis(db=REDIS_TEST_DB)

class CreateRDACoreEntityFromMARCTest(TestCase):

    def setUp(self):
        self.test_rec = pymarc.Record()
        self.test_rec.add_field(pymarc.Field(tag="100",
                                             indicators=["",""],
                                             subfields=["a","Test 100 value"]))
        
        self.root_key = "rdaCore:{0}".format(test_ds.incr("global:rdaCore"))
        json_rule = json.loads('''{"rdaTestRule":{"100":{"subfields":["a"]}}}''')
        self.entity_generator = CreateRDACoreEntityFromMARC(record=self.test_rec,
                                                            redis_server=test_ds,
                                                            root_redis_key=self.root_key,
                                                            entity='Generic',
                                                            json_rules=json_rule)

    def test_init(self):
        self.assertEquals(self.entity_generator.entity_key,
                          "rdaCore:Generic:1")

    def test_generate(self):
        self.entity_generator.generate()
        self.assertEquals(test_ds.hget(self.entity_generator.entity_key,
                                       "rdaTestRule"),
                          "Test 100 value")
        
                                               


    def tearDown(self):
        test_ds.flushdb()

class CreateRDACoreExpressionFromMARCTest(TestCase):

    def setUp(self):
        self.test_rec = pymarc.Record()
        self.test_rec.add_field(pymarc.Field('336',
                                             indicators=['' ,''],
                                             subfields=['a','text','2','marccontent']))
        self.test_rec.add_field(pymarc.Field('130',
                                             indicators=['',''],
                                             subfields=['h','Sound recording']))
        self.test_rec.add_field(pymarc.Field('700',
                                             indicators=['',''],
                                             subfields=['h','Computer Program']))
        self.root_key = "rdaCore:{0}".format(test_ds.incr("global:rdaCore"))
        self.expression_generator = CreateRDACoreExpressionFromMARC(record=self.test_rec,
                                                                    redis_server=test_ds,
                                                                    root_redis_key=self.root_key)
        self.expression_generator.generate()

    def test_init(self):
        self.assertEquals(self.expression_generator.entity_key,
                          "rdaCore:Expression:1")

    def test_content_type(self):
        content_type_key = "{0}:rdaContentType".format(self.expression_generator.entity_key)
        # Tests Expression.contentType in Redis to value in the 336 field
        self.assert_(test_ds.sismember(content_type_key,"text"))
        # Test Expression.contentType in Redis to value in the 130 field
        self.assert_(test_ds.sismember(content_type_key,"Sound recording"))
        # Test Expression.contentType in Redis to value in the 700 field
        self.assert_(test_ds.sismember(content_type_key,"Computer Program"))

    def test__call_number_app__(self):
        pass
        

    def tearDown(self):
        test_ds.flushdb()

class CreateRDACoreItemFromMARCTest(TestCase):

    def setUp(self):
        self.test_rec = pymarc.Record()
        self.test_rec.add_field(pymarc.Field('540',
                                             indicators=['',''],
                                             subfields=['a','Restricted: Copying allowed only for non-profit organizations',
                                                        'b','Colorado College']))
        self.root_key = "rdaCore:{0}".format(test_ds.incr("global:rdaCore"))
        self.item_generator = CreateRDACoreItemFromMARC(record=self.test_rec,
                                                        redis_server=test_ds,
                                                        root_redis_key=self.root_key)
        self.item_generator.generate()

    def test_init(self):
        self.assertEquals(self.item_generator.entity_key,
                          "rdaCore:Item:1")

    def test_restrictions_on_use(self):
        
        restriction_key = "{0}:rdaRestrictionOnUse".format(self.item_generator.entity_key)
        # Tests Item.restrictionOnUse in Redis for 540 subfield a
        self.assert_(test_ds.sismember(restriction_key,
                                       'Restricted: Copying allowed only for non-profit organizations'))
        # Tests Item.restrictionOnUse in Redis for 540 subfield b
        self.assert_(test_ds.sismember(restriction_key,
                                       'Colorado College'))

    def tearDown(self):
        test_ds.flushdb()
        
class CreateRDACoreManifestationFromMARCTest(TestCase):

    def setUp(self):
        self.test_rec = pymarc.Record()
        self.test_rec.add_field(pymarc.Field('007',
                                        data='vd           '))
        self.test_rec.add_field(pymarc.Field('008',
                                             data='100803s20102009nyub\\\\\b\\\\001\0\eng\\'))
        self.test_rec.add_field(pymarc.Field('020',
                                             indicators=['',''],
                                             subfields = ['a','1234-1231']))
        self.test_rec.add_field(pymarc.Field('022',
                                             indicators=['',''],
                                             subfields = ['a','4041453']))
        self.test_rec.add_field(pymarc.Field('024',
                                             indicators=['0',''],
                                             subfields = ['a','US-PR3-73-00012']))
        self.test_rec.add_field(pymarc.Field('024',
                                             indicators=['1',''],
                                             subfields = ['a','781617290183']))
        self.test_rec.add_field(pymarc.Field('024',
                                             indicators=['2',''],
                                             subfields = ['a','979-0-2600-0043-8']))
        self.test_rec.add_field(pymarc.Field('024',
                                             indicators=['3',''],
                                             subfields = ['a','4006381333931']))
        self.test_rec.add_field(pymarc.Field('024',
                                             indicators=['4',''],
                                             subfields = ['a','0095-4403(199502/03)21:3<12:WATIIB>2.0.TX;2-J']))
        self.test_rec.add_field(pymarc.Field('030',
                                             indicators=['',''],
                                             subfields=['a','NATUAS']))
        self.test_rec.add_field(pymarc.Field('074',
                                             indicators=['',''],
                                             subfields=['a','1224']))
        self.test_rec.add_field(pymarc.Field('037',
                                             indicators=['',''],
                                             subfields=['a','001689 E']))
        self.test_rec.add_field(pymarc.Field('086',
                                             indicators=['0',''],
                                             subfields=['a','HE 20.6209:13/45']))
        self.test_rec.add_field(pymarc.Field('086',
                                             indicators=['1',''],
                                             subfields=['a','CS13-211']))
        self.test_rec.add_field(pymarc.Field('245',
                                             indicators=["",""],
                                             subfields=["a",'Test Record Title']))
        self.test_rec.add_field(pymarc.Field('250',
                                             indicators=['',''],
                                             subfields=['a','4th ed.',
                                                        'b','revised by JB Test']))
        self.test_rec.add_field(pymarc.Field('260',
                                             indicators=['',''],
                                             subfields=['c','c2011']))
        self.test_rec.add_field(pymarc.Field('542',
                                             indicators=['',''],
                                             subfields=['g','2012']))
        
        self.root_key = "rdaCore:{0}".format(test_ds.incr("global:rdaCore"))
        self.manifestation_generator = CreateRDACoreManifestationFromMARC(record=self.test_rec,
                                                                          redis_server=test_ds,
                                                                          root_redis_key=self.root_key)
        self.manifestation_generator.generate()
        self.identifiers_key = "{0}:identifiers".format(self.manifestation_generator.entity_key)


    def test_init(self):
        self.assertEquals(self.manifestation_generator.entity_key,
                          "rdaCore:Manifestation:1")


    def test_carrier_type(self):
        # Valid TestCase manifestation_generator
        self.assertEquals(test_ds.hget(self.manifestation_generator.entity_key,
                                       "rdaCarrierType"),
                          "videodisc")  
        
        

    def test_copyright_date(self):
        # Call method in manifestation generator
        copyright_key = "{0}:rdaCopyrightDate".format(self.manifestation_generator.entity_key)
        copyright_dates = list(test_ds.smembers(copyright_key))
        # Tests Manifestation.copyrightDate for 260 field
        self.assertEquals(copyright_dates[0],
                          'c2011')
        # Tests Manifestation.copyrightDate for 008 field
        self.assertEquals(copyright_dates[1],
                          '2010')
        # Tests Manifestation.copyrightDate for 542 field
        self.assertEquals(copyright_dates[2],
                          '2012')

    def test_edition_statement(self):
        # call method in manifestation generator
        edition_key = "{0}:editionStatement".format(self.manifestation_generator.entity_key)
        # Test Manifestation.editionStatement for designations
        self.assertEquals(test_ds.hget(self.manifestation_generator.entity_key,
                                       "rdaDesignationOfEdition"),
                          "4th ed.")
        # Test Manifestation.editionStatement for designation of named revision
        self.assertEquals(test_ds.hget(self.manifestation_generator.entity_key,
                                       "rdaDesignationOfNamedRevisionOfEdition"),
                          'revised by JB Test')

    def test_canadian_govdoc(self):
        self.assertEquals(test_ds.hget(self.identifiers_key,
                                       'Canadian GovDoc'),
                          'CS13-211')

    def test_coden(self):
        self.assertEquals(test_ds.hget(self.identifiers_key,
                                       'CODEN'),
                          'NATUAS')

    
    def test_ean(self):
        self.assertEquals(test_ds.hget(self.identifiers_key,
                                       'EAN'),
                          '4006381333931')

    def test_gpo_item_num(self):
        self.assertEquals(test_ds.hget(self.identifiers_key,
                                       'GPO Item Number'),
                          '1224')

    def test_isbn(self):
        self.assertEquals(test_ds.hget(self.identifiers_key,
                                       'ISBN'),
                          '1234-1231')

    def test_ismn(self):
        self.assertEquals(test_ds.hget(self.identifiers_key,
                                       'ISMN'),
                          '979-0-2600-0043-8')

    def test_isrc(self):
        self.assertEquals(test_ds.hget(self.identifiers_key,
                                       'ISRC'),
                          'US-PR3-73-00012')
        

    def test_issn(self):
        self.assertEquals(test_ds.hget(self.identifiers_key,
                                       'ISSN'),
                          '4041453')

    def test_sic(self):
        self.assertEquals(test_ds.hget(self.identifiers_key,
                                       'SIC'),
                          '0095-4403(199502/03)21:3<12:WATIIB>2.0.TX;2-J')

    def test_stock_num(self):
        self.assertEquals(test_ds.hget(self.identifiers_key,
                                       'Stock number'),
                          '001689 E')

    def test_sudoc(self):
        self.assertEquals(test_ds.hget(self.identifiers_key,
                                       'SuDoc'),
                          'HE 20.6209:13/45')

    def test_title(self):
        title_set_key = test_ds.hget(self.manifestation_generator.entity_key,
                                     "rdaTitle")
        self.assertEquals(''.join(test_ds.smembers(title_set_key)),
                          'Test Record Title')

    def test_upc(self):
        self.assertEquals(test_ds.hget(self.identifiers_key,
                                       'UPC'),
                          '781617290183')
        
        

        

    def tearDown(self):
        test_ds.flushdb()

class CreateRDACoreCreateRDACorePersonsFromMARC(TestCase):

    def setUp(self):
        self.test_rec = pymarc.Record()
        self.test_rec.add_field(pymarc.Field(tag='100',
                                             indicators=["1",""],
                                             subfields=["a","Rosebrough, Robert F."]))
        self.test_rec.add_field(pymarc.Field(tag='700',
                                             indicators=["0",""],
                                             subfields=["a","Whipple, Fred L.",
                                                        "d","1906-2004"]))
        self.test_rec.add_field(pymarc.Field(tag='700',
                                             indicators=["0",""],
                                             subfields=["a","Field, George B.",
                                                        "d","1929-"]))
        self.test_rec.add_field(pymarc.Field(tag='700',
                                             indicators=["0",""],
                                             subfields=["a","Cameron, A. G. W.",
                                                        "d","1925-"]))
        self.person_generator = CreateRDACorePersonsFromMARC(record=self.test_rec,
                                                             redis_server = test_ds)
        self.person_generator.generate()

    def test_init(self):
        self.assertEquals(self.person_generator.people[0],
                          "rdaCore:Person:1")

    def test_preferred_name(self):
        self.assertEquals(test_ds.hget(self.person_generator.people[0],
                                       "rdaPreferredNameForThePerson"),
                          "Rosebrough, Robert F.")
        self.assertEquals(test_ds.hget(self.person_generator.people[1],
                                       "rdaPreferredNameForThePerson"),
                          "Whipple, Fred L.")
        self.assertEquals(test_ds.hget(self.person_generator.people[2],
                                       "rdaPreferredNameForThePerson"),
                          "Field, George B.")
        self.assertEquals(test_ds.hget(self.person_generator.people[3],
                                       "rdaPreferredNameForThePerson"),
                          "Cameron, A. G. W.")

    def test_date_associated_with_person(self):
        self.assertEquals(test_ds.hget(self.person_generator.people[1],
                                       "rdaDateAssociatedWithThePerson"),
                          "1906-2004")
        self.assertEquals(test_ds.hget(self.person_generator.people[2],
                                       "rdaDateAssociatedWithThePerson"),
                          "1929-")
        self.assertEquals(test_ds.hget(self.person_generator.people[3],
                                       "rdaDateAssociatedWithThePerson"),
                          "1925-")
        
    def tearDown(self):
        test_ds.flushdb()

class CreateRDACoreWorkFromMARCTest(TestCase):

    def setUp(self):
        self.test_rec = pymarc.Record()
        self.test_rec.add_field(pymarc.Field(tag='130',
                                             indicators=["",""],
                                             subfields=["a","2012"]))
        self.test_rec.add_field(pymarc.Field(tag='240',
                                             indicators=["",""],
                                             subfields=["f","2011"]))
        self.root_key = "rdaCore:{0}".format(test_ds.incr("global:rdaCore"))
        self.work_generator = CreateRDACoreWorkFromMARC(record=self.test_rec,
                                                        redis_server=test_ds,
                                                        root_redis_key=self.root_key)
        self.work_generator.generate()

    def test_init(self):
        self.assertEquals(self.work_generator.entity_key,
                          "rdaCore:Work:1")

    def test_date_of_work(self):
        dow_key = test_ds.hget(self.work_generator.entity_key,
                               "rdaDateOfWork")
        self.assert_(test_ds.sismember(dow_key,
                                       "2012"))
        self.assert_(test_ds.sismember(dow_key,
                                       "2011"))

    def tearDown(self):
        test_ds.flushdb()
        

class MARCRulesTest(TestCase):

    def setUp(self):
        pass

    def test_get_position_values(self):
        test_rule = json.loads('''{"positions": {"start": "0", "end": "1"}}''')
        marc_rule = MARCRules(json_rules=test_rule)
        valid007 = pymarc.Field(tag='007',indicators=["",""],data='ca   00000')
        self.assertEquals(marc_rule.__get_position_values__(test_rule,valid007),
                          'ca')
        valid245 = pymarc.Field(tag='245',indicators=["",""],subfields=['a','Test Title'])
        self.assertEquals(marc_rule.__get_position_values__(test_rule,valid245),
                          None)

    def test_get_subfields(self):
        test_rule = json.loads('''{"subfields": ["a"]}''')
        marc_rule = MARCRules(json_rules=test_rule)
        valid245 = pymarc.Field(tag='245',indicators=["",""],subfields=['a','Test Title'])
        self.assertEquals(marc_rule.__get_subfields__(test_rule,valid245),
                          ['Test Title'])
        valid007 = pymarc.Field(tag='007',indicators=["",""],data='ca   00000')
        self.assertEquals(marc_rule.__get_subfields__(test_rule,valid007),
                          None)
        test_multiple_rule = json.loads('''{"subfields":["a","c"]}''')
        valid300 = pymarc.Field(tag='300',
                                indicators=["",""],
                                subfields=['a','204 p. ;','c','22cm.'])
        marc_multiple_rule = MARCRules(json_rules=test_multiple_rule)
        self.assertEquals(marc_multiple_rule.__get_subfields__(test_multiple_rule,
                                                               valid300),
                          ['204 p. ;','22cm.'])

    def test_test_subfields(self):
        test_rule = json.loads('''{"subfields":["a","b"],
          "condition": "lambda x: ''.join(x.get_subfields('2')) == 'marccontent'"}''')
        marc_rule = MARCRules(json_rules=test_rule)
        valid336 = pymarc.Field(tag='336',
                                indicators=["",""],
                                subfields=["a","text",
                                           "2","marccontent"])
        self.assert_(marc_rule.__test_subfield__(test_rule,valid336))
        
        

    def test_load_marc(self):
        test_record = pymarc.Record()
        test_record.add_field(pymarc.Field(tag='008',
                                           data='850611s1985\\\\nyu\\\\\\\\\\\000\1\eng\\'))
        test_record.add_field(pymarc.Field(tag='035',
                                           indicators=["",""],
                                           subfields=['a','(CoCC)1000']))
        test_record.add_field(pymarc.Field(tag='100',
                                           indicators=["1",""],
                                           subfields=['a','Grau, Shirley Ann.']))
        test_record.add_field(pymarc.Field(tag='300',
                                           indicators=["",""],
                                           subfields=['a','204 p. ;','c','22cm.']))
        json_rule_set = json.loads('''{"rdaExtentOfManifestation": {"300": {"subfields": ["a","c"]}},
                                    "rdaPreferredNameForThePerson": {"100": {"indicators": {"0": ["0", "1"]},
                                                                             "subfields": ["a"]}},
                                    "rdaCopyrightDate": {"008": {"positions": {"start": "7","end":10}}}}''')
        marc_rules = MARCRules(json_rules=json_rule_set)
        marc_rules.load_marc(test_record)
        self.assertEquals(marc_rules.json_results["rdaCopyrightDate"],
                          ["1985"])
        self.assertEquals(marc_rules.json_results["rdaExtentOfManifestation"],
                          ["204 p. ;","22cm."])
        self.assertEquals(marc_rules.json_results["rdaPreferredNameForThePerson"],
                          ['Grau, Shirley Ann.'])

    def test_test_position_values(self):
        field008 = pymarc.Field(tag='008',
                                data='850611s1985\\\\nyu\\\\\\\\\\\000\1\eng\\')
        test_rule = json.loads('''{"positions": {"start": "7","end":10},"condition":"lambda x: x[6] == 's'"}''')
        marc_rules = MARCRules(json_rules=test_rule)
        self.assert_(marc_rules.__test_position_values__(test_rule,field008))
        

        
    def tearDown(self):
        test_ds.flushdb()
