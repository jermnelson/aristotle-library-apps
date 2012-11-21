"""
 :mod:`tests` - Unit tests for the Bibliographic Framework App
"""
import redis,pymarc
from django.test import TestCase
from marcr_models import *
from ingesters import MARC21toInstance,MARC21toMARCR,MARC21toPerson,MARC21toWork
from ingesters import MARC21toFacets

try:
    from aristotle.settings import TEST_REDIS
except ImportError, e:
    TEST_REDIS = redis.StrictRedis(host="192.168.64.143",port=6385)
    
test_redis = TEST_REDIS



class MARCRModelTest(TestCase):

    def setUp(self):
        self.base_bibframe = MARCRModel(redis=test_redis,
                                        redis_key='marcr:1')
        self.empty_base_bibframe = MARCRModel()
        
    
    def test_init(self):
        """
        Tests initalization of base class
        """
        self.assert_(self.base_bibframe.redis is not None)
        self.assertEquals(self.base_bibframe.redis_key,
                          'marcr:1')
        self.assertEquals(self.base_bibframe.attributes,{})
        self.assert_(self.empty_base_bibframe.redis is None)
        self.assert_(self.empty_base_bibframe.redis_key is None)
        self.assertEquals(self.empty_base_bibframe.attributes,{})

    def test_save(self):
        self.base_bibframe.save()
        self.assert_(test_redis.hget(self.base_bibframe.redis_key,
                                     "created"))
        self.assertEquals(self.base_bibframe.attributes['created'],
                          test_redis.hget(self.base_bibframe.redis_key,
                                          "created"))
        

    def tearDown(self):
        test_redis.flushdb()

class AuthorityTest(TestCase):

    def setUp(self):
        self.new_base_authority = Authority(redis=test_redis)
        self.base_authority = Authority(redis=test_redis,
                                        redis_key="marcr:Authority:1")

    def test_init(self):
	self.assert_(self.new_base_authority.redis is not None)
        self.assertEquals(self.base_authority.redis_key,
                          "marcr:Authority:1")

    def tearDown(self):
        test_redis.flushdb()

class MARC21toFacetsTest(TestCase):

    def setUp(self):
	self.facet_ingester = MARC21toFacets(annotation_ds=test_redis,
			                     authority_ds=test_redis,
					     instance_ds=test_redis,
					     work_ds=test_redis)

    def test_access_facet(self):
	instance = Instance(redis=test_redis)
	instance.save()
	marc_record = pymarc.Record()
	marc_record.add_field(pymarc.Field(tag='994',
		                           indicators=[' ',' '],
					   subfields=['a','ewww']))
	self.facet_ingester.add_access_facet(instance,marc_record)
	self.assert_(test_redis.exists("marcr:Annotation:Facet:Access:Online"))
	self.assert_(test_redis.sismember("marcr:Annotation:Facet:Access:Online",instance.redis_key))


    def test_format_facet(self):
        instance = Instance(redis=test_redis,
			    attributes={"rda:carrierTypeManifestation":"Book"})
	instance.save()
	self.facet_ingester.add_format_facet(instance)
	self.assert_(test_redis.exists("marcr:Annotation:Facet:Format:Book"))
	self.assert_(test_redis.sismember("marcr:Annotation:Facet:Format:Book",instance.redis_key))

    def test_lc_facet(self):
	work = Work(redis=test_redis)
	work.save()
	marc_record = pymarc.Record()
	marc_record.add_field(pymarc.Field(tag='050',
		                           indicators=['0','0'],
					   subfields=['a','QA345','b','T6']))
        self.facet_ingester.add_lc_facet(work,marc_record)
	self.assert_(test_redis.exists("marcr:Annotation:Facet:LOCFirstLetter:QA"))
	self.assert_(test_redis.sismember("marcr:Annotation:Facet:LOCFirstLetter:QA",work.redis_key))
	self.assertEquals(test_redis.hget("marcr:Annotation:Facet:LOCFirstLetters","QA"),
                          "QA - Mathematics")

    def test_location_facet(self):
	instance = Instance(redis=test_redis)
	instance.save()
        marc_record = pymarc.Record()
	marc_record.add_field(pymarc.Field(tag='994',
		                           indicators=['0','0'],
					   subfields=['a','ewwwn']))
	marc_record.add_field(pymarc.Field(tag='994',
		                           indicators=['0','0'],
					   subfields=['a','tarfc']))
	marc_record.add_field(pymarc.Field(tag='994',
		                           indicators=['0','0'],
					   subfields=['a','tgr']))
	self.facet_ingester.add_location_facet(instance,marc_record)
	self.assert_(test_redis.exists("marcr:Annotation:Facet:Location:ewwwn"))
	self.assert_(test_redis.exists("marcr:Annotation:Facet:Location:tarfc"))
	self.assert_(test_redis.exists("marcr:Annotation:Facet:Location:tgr"))
	self.assertEquals(test_redis.hget("marcr:Annotation:Facet:Locations","ewwwn"),
			  "Online")
	self.assertEquals(test_redis.hget("marcr:Annotation:Facet:Locations","tarfc"),
                          "Tutt Reference")





    def tearDown(self):
        test_redis.flushdb()



class MARC21toInstanceTest(TestCase):

    def setUp(self):
        marc_record = pymarc.Record()
        marc_record.add_field(pymarc.Field(tag='050',
                                           indicators=['0','0'],
                                           subfields=['a','QC861.2',
                                                      'b','.B36']))
        marc_record.add_field(pymarc.Field(tag='086',
                                           indicators=['0',' '],
                                           subfields=['a','HE 20.6209:13/45']))
        marc_record.add_field(pymarc.Field(tag='099',
                                           indicators=[' ',' '],
                                           subfields=['a','Video 6716']))
        marc_record.add_field(pymarc.Field(tag='907',
                                           indicators=[' ',' '],
                                           subfields=['a','.b1112223x']))
        self.instance_ingester = MARC21toInstance(annotation_ds=test_redis,
                                                  authority_ds=test_redis,
                                                  instance_ds=test_redis,
                                                  marc_record=marc_record,
                                                  work_ds=test_redis)
        self.instance_ingester.ingest()

    def test_init(self):
        self.assert_(self.instance_ingester.instance.redis_key)

    def test_lccn(self):
        self.assertEquals(self.instance_ingester.instance.attributes['rda:identifierForTheManifestation']['lccn'],
                          'QC861.2 .B36')    
        self.assertEquals(self.instance_ingester.instance.attributes['rda:identifierForTheManifestation']['lccn'],
                          test_redis.hget("{0}:rda:identifierForTheManifestation".format(self.instance_ingester.instance.redis_key),
                                          "lccn"))

    def test_local(self):
        self.assertEquals(self.instance_ingester.instance.attributes['rda:identifierForTheManifestation']['local'],
                          'Video 6716')
        self.assertEquals(self.instance_ingester.instance.attributes['rda:identifierForTheManifestation']['local'],
                          test_redis.hget("{0}:rda:identifierForTheManifestation".format(self.instance_ingester.instance.redis_key),
                                          "local"))

    def test_ils_bib_number(self):
        self.assertEquals(self.instance_ingester.instance.attributes['rda:identifierForTheManifestation']['ils-bib-number'],
                          'b1112223')
        self.assertEquals(self.instance_ingester.instance.attributes['rda:identifierForTheManifestation']['ils-bib-number'],
                          test_redis.hget("{0}:rda:identifierForTheManifestation".format(self.instance_ingester.instance.redis_key),
                                          'ils-bib-number'))

    def test_sudoc(self):
        self.assertEquals(self.instance_ingester.instance.attributes['rda:identifierForTheManifestation']['sudoc'],
                          'HE 20.6209:13/45')
        self.assertEquals(self.instance_ingester.instance.attributes['rda:identifierForTheManifestation']['sudoc'],
                          test_redis.hget("{0}:rda:identifierForTheManifestation".format(self.instance_ingester.instance.redis_key),
                                          "sudoc"))
        
    def tearDown(self):
        test_redis.flushdb()

class MARC21toMARCRTest(TestCase):

    def setUp(self):
        marc_record = pymarc.Record()
        marc_record.add_field(pymarc.Field(tag='245',
                                           indicators=['1','0'],
                                           subfields=['a','Statistics:',
                                                      'b','facts or fiction.']))
        marc_record.add_field(pymarc.Field(tag='050',
                                           indicators=['0','0'],
                                           subfields=['a','QC861.2',
                                                      'b','.B36']))
        marc_record.add_field(pymarc.Field(tag='907',
                                           indicators=[' ',' '],
                                           subfields=['a','.b1112223x']))
        self.marc21_ingester =  MARC21toMARCR(annotation_ds=test_redis,
                                              authority_ds=test_redis,
                                              instance_ds=test_redis,
                                              marc_record=marc_record,
                                              work_ds=test_redis)
        self.marc21_ingester.ingest()

    def test_init(self):
        self.assert_(self.marc21_ingester.marc2work.work.redis_key)
        self.assert_(self.marc21_ingester.marc2instance.instance.redis_key)

    def test_instance_work(self):
        self.assertEquals(self.marc21_ingester.marc2instance.instance.attributes['marcr:Work'],
                          self.marc21_ingester.marc2work.work.redis_key)

    def test_work_instance(self):
        self.assertEquals(list(self.marc21_ingester.marc2work.work.attributes['marcr:Instances'])[0],
                          self.marc21_ingester.marc2instance.instance.redis_key)


    def tearDown(self):
        test_redis.flushdb()


class MARC21toPersonTest(TestCase):

    def setUp(self):
        field100 = pymarc.Field(tag='100',
                                indicators=['1','0'],
                                subfields=['a','Austen, Jane',
                                           'd','1775-1817'])
        self.person_ingester = MARC21toPerson(annotation_ds=test_redis,
                                              authority_ds=test_redis,
                                              field=field100,
                                              instance_ds=test_redis,
                                              work_ds=test_redis)
        self.person_ingester.ingest()

    def test_init(self):
        self.assert_(self.person_ingester.person.redis_key)

    def test_dob(self):
        self.assertEquals(self.person_ingester.person.attributes['rda:dateOfBirth'],
                          '1775')
        self.assertEquals(self.person_ingester.person.attributes['rda:dateOfBirth'],
                          test_redis.hget(self.person_ingester.person.redis_key,
                                          'rda:dateOfBirth'))

    def test_dod(self):
        self.assertEquals(self.person_ingester.person.attributes['rda:dateOfDeath'],
                          '1817')
        self.assertEquals(self.person_ingester.person.attributes['rda:dateOfDeath'],
                          test_redis.hget(self.person_ingester.person.redis_key,
                                          'rda:dateOfDeath'))

    def test_preferred_name(self):
        self.assertEquals(self.person_ingester.person.attributes['rda:preferredNameForThePerson'],
                          'Austen, Jane')
        self.assertEquals(self.person_ingester.person.attributes['rda:preferredNameForThePerson'],
                          test_redis.hget(self.person_ingester.person.redis_key,
                                          'rda:preferredNameForThePerson'))
                                                           

    def tearDown(self):
        test_redis.flushdb()
        
        

class MARC21toWorkTest(TestCase):

    def setUp(self):
        marc_record = pymarc.Record()
        marc_record.add_field(pymarc.Field(tag='245',
                                           indicators=['1','0'],
                                           subfields=['a','Statistics:',
                                                      'b','facts or fiction.']))
        self.work_ingester = MARC21toWork(annotation_ds=test_redis,
                                          authority_ds=test_redis,
                                          instance_ds=test_redis,
                                          marc_record=marc_record,
                                          work_ds=test_redis)
        self.work_ingester.ingest()

    def test_init(self):
        self.assert_(self.work_ingester.work.redis_key)

    def test_metaphone(self):
        self.assertEquals(self.work_ingester.work.attributes['rda:Title']["phonetic"],
                          "STTSTKSFKTSARFKXN")
        self.assertEquals(self.work_ingester.work.attributes['rda:Title']["phonetic"],
                          test_redis.hget("{0}:{1}".format(self.work_ingester.work.redis_key,
                                                           'rda:Title'),
                                          "phonetic"))
    

    def test_title(self):
        self.assertEquals(self.work_ingester.work.attributes['rda:Title']['rda:preferredTitleForTheWork'],
                          'Statistics: facts or fiction.')
        self.assertEquals(self.work_ingester.work.attributes['rda:Title']['rda:preferredTitleForTheWork'],
                          test_redis.hget("{0}:{1}".format(self.work_ingester.work.redis_key,
                                                           'rda:Title'),
                                          'rda:preferredTitleForTheWork'))

    def tearDown(self):
        test_redis.flushdb()    
        

class PersonAuthorityTest(TestCase):

    def setUp(self):
        self.person = Person(redis=test_redis,
                             attributes={'rda:dateOfBirth':'1962-04-21',
                                         'rda:dateOfDeath':'2008-09-12',
                                         'rda:gender':'male',
                                         'rda:preferredNameForThePerson':'Wallace, David Foster',
                                         'rda:identifierFor':{'loc':'http://id.loc.gov/authorities/names/n86001949'}})
        self.person.save()

    def test_dateOfBirth(self):
        self.assertEquals(self.person.attributes['rda:dateOfBirth'],
                          test_redis.hget(self.person.redis_key,
                                          'rda:dateOfBirth'))

    def test_dateOfDeath(self):
        self.assertEquals(self.person.attributes['rda:dateOfDeath'],
                          test_redis.hget(self.person.redis_key,
                                          'rda:dateOfDeath'))

    def test_init(self):
        self.assert_(self.person.redis is not None)
        

    def test_gender(self):
        self.assertEquals(self.person.attributes['rda:gender'],
                          test_redis.hget(self.person.redis_key,
                                          'rda:gender'))

    def test_loc_id(self):
        self.assertEquals(self.person.attributes['rda:identifierFor']['loc'],
                          test_redis.hget("{0}:{1}".format(self.person.redis_key,
                                                           'rda:identifierFor'),
                                          'loc'))

    def test_name(self):
        self.assertEquals(self.person.attributes['rda:preferredNameForThePerson'],
                          test_redis.hget(self.person.redis_key,
                                          'rda:preferredNameForThePerson'))

    

    
    def test_save(self):
        self.assertEquals(self.person.redis_key,
                          "marcr:Authority:Person:1")

    def tearDown(self):
        test_redis.flushdb()

class InstanceTest(TestCase):

    def setUp(self):
        existing_attributes = {'rda:publisher':'marcr:Authority:CorporateBody:1',
                               'rda:identifierForTheManifestation':{'lccn':'C1.D11',
                                                                    'local':'Video 6716'}}
        new_attributes = {'rda:publisher':'marcr:Authority:CorporateBody:2',
                          'rda:identifierForTheManifestation':{'ils-bib-number':'b1762075',
                                                               'sudoc':'HD1695.C7C55 2007'}}
        self.instance = Instance(redis=test_redis,
                                 redis_key="marcr:Instance:2",
                                 attributes=existing_attributes)        
        self.new_instance = Instance(redis=test_redis,
                                     attributes=new_attributes)
        

    def test_ils_bib_number(self):
        self.new_instance.save()
        self.assertEquals(self.new_instance.attributes['rda:identifierForTheManifestation']['ils-bib-number'],
                          test_redis.hget("{0}:{1}".format(self.new_instance.redis_key,
                                                           'rda:identifierForTheManifestation'),
                                          "ils-bib-number"))

    def test_init(self):
        self.assert_(self.new_instance.redis)
        self.assert_(self.new_instance.redis_key is None)
        self.assert_(self.instance.redis)
        self.assertEquals(self.instance.redis_key,
                          "marcr:Instance:2")

    def test_lccn_callnumber(self):
        self.instance.save()
        self.assertEquals(self.instance.attributes['rda:identifierForTheManifestation']['lccn'],
                          test_redis.hget("{0}:{1}".format(self.instance.redis_key,
                                                           'rda:identifierForTheManifestation'),
                                          "lccn"))

    def test_local_callnumber(self):
        self.instance.save()
        self.assertEquals(self.instance.attributes['rda:identifierForTheManifestation']['local'],
                          test_redis.hget("{0}:{1}".format(self.instance.redis_key,
                                                           'rda:identifierForTheManifestation'),
                                          "local"))

    def test_publisher(self):
        self.new_instance.save()
        self.instance.save()
        self.assertEquals(self.new_instance.attributes['rda:publisher'],
                          'marcr:Authority:CorporateBody:2')
        self.assertEquals(self.instance.attributes['rda:publisher'],
                          'marcr:Authority:CorporateBody:1')

    def test_sudoc_callnumber(self):
        self.new_instance.save()
        self.assertEquals(self.new_instance.attributes['rda:identifierForTheManifestation']['sudoc'],
                          test_redis.hget("{0}:{1}".format(self.new_instance.redis_key,
                                                           'rda:identifierForTheManifestation'),
                                          "sudoc"))
                

    def tearDown(self):
        test_redis.flushdb()

class WorkTest(TestCase):

    def setUp(self):
        new_attributes = {'rda:dateOfWork':2012,
                          'rda:isCreatedBy':'Authority:Person:1'}
        # Test work w/o Redis key (new Work)
        self.new_work = Work(redis=test_redis,
                             attributes=new_attributes)
        existing_attributes = {'rda:dateOfWork':1999,
                               'rda:isCreatedBy':'Authority:CorporateBody:1'}
        # Tests work w/pre-existing Redis key
        self.work = Work(redis=test_redis,
                         redis_key="marcr:Work:2",
                         attributes=existing_attributes)

    def test_init_(self):
        self.assert_(self.new_work.redis)
        self.assert_(self.new_work.redis_key is None)
        self.assert_(self.work.redis)
        self.assertEquals(self.work.redis_key,
                          "marcr:Work:2")

    def test_dateOfWork(self):
        self.new_work.save()
        self.work.save()
        self.assertEquals(str(self.new_work.attributes['rda:dateOfWork']),
                          test_redis.hget(self.new_work.redis_key,
                                          "rda:dateOfWork"))
        self.assertEquals(str(self.work.attributes['rda:dateOfWork']),
                          test_redis.hget(self.work.redis_key,
                                          'rda:dateOfWork'))

    def test_isCreatedBy(self):
        self.new_work.save()
        self.work.save()
        self.assertEquals(self.new_work.attributes['rda:isCreatedBy'],
                          'Authority:Person:1')
        self.assertEquals(self.work.attributes['rda:isCreatedBy'],
                          'Authority:CorporateBody:1')
                          

    def test_save(self):
        self.new_work.save()
        self.work.save()
        self.assertEquals(self.new_work.redis_key,"marcr:Work:1")
        self.assert_(test_redis.hget(self.work.redis_key,
                                     'created'))
        # Extracting just the year-month-day to test
        self.assertEquals(self.new_work.attributes['created'].split(":")[0],
                          test_redis.hget(self.work.redis_key,
                                          'created').split(":")[0])
        self.assert_(test_redis.exists(self.work.redis_key))
        

    
                                          

    def tearDown(self):
        test_redis.flushdb()
        
        
                                   
        
        
