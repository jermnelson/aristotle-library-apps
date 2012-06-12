"""
 :mod:`tests` Unit Tests for MARC Batch App functionality 
"""
__author__ = "Jeremy Nelson"
import redis,pymarc,datetime
from django.test import TestCase
from aristotle.settings import REDIS_TEST_DB
from jobs.frbr_redis import *


test_ds = redis.StrictRedis(db=REDIS_TEST_DB)

class CreateRDACoreEntityFromMARCTest(TestCase):

    def setUp(self):
        self.test_rec = pymarc.Record()
        self.root_key = "rdaCore:{0}".format(test_ds.incr("global:rdaCore"))
        self.entity_generator = CreateRDACoreEntityFromMARC(record=self.test_rec,
                                                            redis_server=test_ds,
                                                            root_redis_key=self.root_key,
                                                            entity='Generic')

    def test_init(self):
        self.assertEquals(self.entity_generator.entity_key,
                          "{0}:Generic:1".format(self.root_key))
                                               

    def test_add_attribute(self):
        self.entity_generator.__add_attribute__("name",["testing",])
        # Name should be a hash key because it is a singleton
        self.assert_(test_ds.hexists(self.entity_generator.entity_key,
                                     "name"))
        self.assertEquals(test_ds.hget(self.entity_generator.entity_key,
                                       "name"),
                          "testing")
        self.entity_generator.__add_attribute__("name",["testing two",])
        # Hash value for attribute should now be deleted
        self.assert_(not test_ds.hexists(self.entity_generator.entity_key,
                                         "name"))
        # Set should now exist for entity
        entity_attribute_set_key = "{0}:{1}".format(self.entity_generator.entity_key,"name")
        self.assert_(test_ds.exists(entity_attribute_set_key))
  

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

    def test_init(self):
        self.assertEquals(self.expression_generator.entity_key,
                          "{0}:Expression:1".format(self.root_key))

    def test_content_type(self):
        # Calls method in generator
        self.expression_generator.__content_type__()
        content_type_key = "{0}:contentType".format(self.expression_generator.entity_key)
        # Tests Expression.contentType in Redis to value in the 336 field
        self.assert_(test_ds.sismember(content_type_key,"text"))
        # Test Expression.contentType in Redis to value in the 130 field
        self.assert_(test_ds.sismember(content_type_key,"Sound recording"))
        # Test Expression.contentType in Redis to value in the 700 field
        self.assert_(test_ds.sismember(content_type_key,"Computer Program"))
        

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

    def test_init(self):
        self.assertEquals(self.item_generator.entity_key,
                          "{0}:Item:1".format(self.root_key))

    def test_restrictions_on_use(self):
        # Call method in item generator
        self.item_generator.__restrictions_on_use__()
        restriction_key = "{0}:restrictionsOnUse".format(self.item_generator.entity_key)
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
                                             subfields = ['a','4041453']))
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


    def test_init(self):
        self.assertEquals(self.manifestation_generator.entity_key,
                          "{0}:Manifestation:1".format(self.root_key))


    def test_carrier_type(self):
        # Valid TestCase manifestation_generator
        self.manifestation_generator.__carrier_type__()
        self.assertEquals(test_ds.hget(self.manifestation_generator.entity_key,
                                       "carrierType"),
                          "videodisc")
        # Create stub MARC record with multiple carrier type encodings
        test_rec = pymarc.Record()
        test_rec.add_field(pymarc.Field('007',
                                        data='cr        '))
        test_rec.add_field(pymarc.Field('300',
                                        indicators=['',''],
                                        subfields=['f','volume']))
        test_rec.add_field(pymarc.Field('338',
                                        indicators=['',''],
                                        subfields=['a',"film roll"]))
        root_key = "rdaCore:{0}".format(test_ds.incr("global:rdaCore"))
        manifestation_generator = CreateRDACoreManifestationFromMARC(record=test_rec,
                                                                     redis_server=redis_server,
                                                                     root_redis_key=root_key)
        
        manifestation_generator.__carrier_type__()
##        # Now test various iterations of carrier types in record
        carrier_key = '{0}:carrierType'.format(manifestation_generator.entity_key)
        print("{0} exists={1}".format(carrier_key,test_ds.exists(carrier_key)))
##        carrier_types = test_ds.smembers()
##        self.assertEquals(carrier_types[0],
##                          "online resource")
##        self.assertEquals(carrier_types[1],
##                          "volume")
##        self.assertEquals(carrier_types[2],
##                          "film roll")
                                       
                                        
        
        

    def test_copyright_date(self):
        # Call method in manifestation generator
        self.manifestation_generator.__copyright_date__()
        copyright_key = "{0}:copyrightDate".format(self.manifestation_generator.entity_key)
        copyright_dates = test_ds.zrange(copyright_key,0,-1)
        # Tests Manifestation.copyrightDate for 008 field
        self.assertEquals(copyright_dates[0],
                          '2009')
        # Tests second Manifestation.copyrightDate for 008 field
        self.assertEquals(copyright_dates[1],
                          '2010')
        # Tests third Manifestation.copyrightDate for 260 field
        self.assertEquals(copyright_dates[2],
                          '2011')
        # Tests forth Manifestation.copyrightDate for 542 field
        self.assertEquals(copyright_dates[3],
                          '2012')

    def test_edition_statement(self):
        # call method in manifestation generator
        self.manifestation_generator.__edition_statement__()
        edition_key = "{0}:editionStatement".format(self.manifestation_generator.entity_key)
        # Test Manifestation.editionStatement for designations
        designation_key = test_ds.hget(edition_key,"designationOfEdition")
        self.assert_(test_ds.sismember(designation_key,"4th ed."))
        # Test Manifestation.editionStatement for designation of named revision
        named_key = test_ds.hget(edition_key,"designationOfNamedRevisionOfEdition")
        self.assert_(test_ds.sismember(named_key,'revised by JB Test'))

    def test_all_identifiers(self):
        """
        Method creates an very artificial MARC records with all of the different identifiers
        set for testing
        """
        test_id_rec = pymarc.Record()
        # ISSN
        test_id_rec.add_field(pymarc.Field('022',
                                           indicators=['',''],
                                           subfields = ['a','1234-1231']))
        # ISRC
        test_id_rec.add_field(pymarc.Field('024',
                                           indicators=['0',''],
                                           subfields = ['a','US-PR3-73-00012']))
        # UPC
        test_id_rec.add_field(pymarc.Field('024',
                                           indicators=['1',''],
                                           subfields = ['a','781617290183']))
        manifestation_generator = CreateRDACoreManifestationFromMARC(record=test_id_rec,
                                                                     redis_server=test_ds,
                                                                     root_redis_key="rdaCore:{0}".format(test_ds.incr("global:rdaCore")))
        identifiers_key = "{0}:identifiers".format(manifestation_generator.entity_key)
        values_hash_key = "{0}:values".format(identifiers_key)
        # Test ISSN
        self.assertEquals(test_ds.hget(values_hash_key,
                                       'issn'),
                          '1234-1231')
        # Test ISRC
        self.assertEquals(test_ds.hget(values_hash_key,
                                       'isrc'),
                          'US-PR3-73-00012')
        # Test UPC
        self.assertEquals(test_ds.get(values_hash_key,
                                      'upc'),
                          '781617290183')
        

    def test_isbn(self):
        # call method in manifestation generator
        self.manifestation_generator.__identifiers__()
        identifiers_key = "{0}:identifiers".format(self.manifestation_generator.entity_key)
        self.assertEquals(test_ds.hget('{0}:values'.format(identifiers_key),
                                       'isbn'),
                          '4041453')
        

    def tearDown(self):
        test_ds.flushdb()

                                

    
