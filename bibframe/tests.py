"""
 :mod:`tests` - Unit tests for the Bibliographic Framework App
"""
__author__ = "Jeremy Nelson"
import pymarc
import os
import redis
from django.test import TestCase
from bibframe.models import *
from aristotle.settings import PROJECT_HOME

try:
    from aristotle.settings import TEST_REDIS
except ImportError, e:
    TEST_REDIS = redis.StrictRedis(host="192.168.64.143",
                                   port=6385)

test_redis = TEST_REDIS

class ProcessKeyTest(TestCase):

    def setUp(self):
	self.timestamp = datetime.datetime.utcnow().isoformat()
        test_redis.hset('bf:CreativeWork:1',
			'created_on',
			self.timestamp)


    def test_process_key(self):
	self.assertEquals(process_key('bf:CreativeWork:1', test_redis)['created_on'],
			              self.timestamp)

	
##    def test_process_key_exception(self):
##        self.assertRaises(,
##                          process_key,
##                          'bf:CreativeWork:2', 
##                          test_redis)

    def tearDown(self):
        test_redis.flushdb()

class SaveKeysTest(TestCase):

    def setUp(self):
        save_keys('test:entity:1','option',1,test_redis)
        save_keys('test:entity:1','option2',set([2,]),test_redis)
        save_keys('test:entity:1','option3',set([3,4]),test_redis)


    def test_save_keys_string(self):
        self.assertEquals(test_redis.hget('test:entity:1','option'),
                          '1')

    def test_save_keys_set(self):
        self.assertEquals(test_redis.hget('test:entity:1','option2'),
                          '2')
        self.assertEquals(test_redis.smembers('test:entity:1:option3'),
                          set(['3','4']))
    

    def tearDown(self):
        test_redis.flushdb()

class RedisBibframeInterfaceTest(TestCase):

    def setUp(self):
        self.minimal_instance = RedisBibframeInterface()

    def test_init(self):
        self.assert_(not self.minimal_instance.primary_redis)
	self.assert_(not self.minimal_instance.redis_key)

    def test_save_execeptions(self):
	self.assertRaises(ValueError,self.minimal_instance.save)

    def tearDown(self):
        test_redis.flushdb()

class TestResource(TestCase):

    def setUp(self):
        self.resource = Resource(primary_redis=test_redis)

    def test_init(self):
        self.assert_(self.resource.primary_redis is not None)

    def tearDown(self):
        test_redis.flushdb()
        

class TestAuthority(TestCase):

    def setUp(self):
        self.new_base_authority = Authority(primary_redis=test_redis)
	self.created_on = datetime.datetime.utcnow().isoformat()
	test_redis.hset('bibframe:Authority:1','created_on',self.created_on)
        self.base_authority = Authority(primary_redis=test_redis,
                                        redis_key="bibframe:Authority:1",
                                        hasAnnotation=set('bibframe:Annotation:1'))
	self.base_authority.save()

    def test_init(self):
	self.assert_(self.new_base_authority.primary_redis is not None)
	self.assert_(test_redis.exists(self.base_authority.redis_key))
        self.assertEquals(self.base_authority.redis_key,
                          "bibframe:Authority:1")

    def test_hasAnnotation(self):
        self.assertEquals(self.base_authority.hasAnnotation,
                          set('bibframe:Annotation:1'))
	self.assertEquals(test_redis.smembers('bibframe:Authority:1:hasAnnotation'),
			  set('bibframe:Annotation:1'))

    def tearDown(self):
        test_redis.flushdb()

class TestPersonAuthority(TestCase):

    def setUp(self):
        self.person = Person(primary_redis=test_redis,
                             identifier={'loc':'http://id.loc.gov/authorities/names/n86001949'},
                             label="David Foster Wallace",
                             hasAnnotation=set('bibframe:Annotation:1'),
                             isni='0000 0001 1768 6131')
        setattr(self.person,'rda:dateOfBirth','1962-04-21')
        setattr(self.person,'rda:dateOfDeath','2008-09-12')
        setattr(self.person,'rda:gender','male')
        setattr(self.person,'foaf:familyName','Wallace')
        setattr(self.person,'foaf:givenName','David')
        setattr(self.person,'rda:preferredNameForThePerson','Wallace, David Foster')
        self.person.save()

    def test_dateOfBirth(self):
        self.assertEquals(getattr(self.person,'rda:dateOfBirth'),
                          test_redis.hget(self.person.redis_key,
                                          'rda:dateOfBirth'))

    def test_dateOfDeath(self):
        self.assertEquals(getattr(self.person,'rda:dateOfDeath'),
                          test_redis.hget(self.person.redis_key,
                                          'rda:dateOfDeath'))
    def test_hasAnnotation(self):
        self.assertEquals(self.person.hasAnnotation,
                          set('bibframe:Annotation:1'))

    def test_init(self):
        self.assert_(self.person.primary_redis is not None)

    def test_isni(self):
        self.assertEquals(self.person.isni,
                          '0000 0001 1768 6131')

    def test_foaf(self):
        self.assertEquals(getattr(self.person,'foaf:givenName'),
                          'David')
        self.assertEquals(getattr(self.person,'foaf:givenName'),
                          test_redis.hget(self.person.redis_key,
                                          'foaf:givenName'))
        self.assertEquals(getattr(self.person,'foaf:familyName'),
                          'Wallace')
        self.assertEquals(getattr(self.person,'foaf:familyName'),
                          test_redis.hget(self.person.redis_key,
                                          'foaf:familyName'))
      

    def test_gender(self):
        self.assertEquals(getattr(self.person,'rda:gender'),
                          test_redis.hget(self.person.redis_key,
                                          'rda:gender'))

    def test_label(self):
        self.assertEquals(self.person.label,
                          "David Foster Wallace")

    def test_loc_id(self):
        self.assertEquals(self.person.identifier.get('loc'),
                          test_redis.hget("{0}:{1}".format(self.person.redis_key,
                                                           'identifier'),
                                          'loc'))

    def test_name(self):
        self.assertEquals(getattr(self.person,'rda:preferredNameForThePerson'),
                          test_redis.hget(self.person.redis_key,
                                          'rda:preferredNameForThePerson'))

    def test_save(self):
        self.assertEquals(self.person.redis_key,
                          "bibframe:Person:1")

    def tearDown(self):
        test_redis.flushdb()

        
class TestInstance(TestCase):

    def setUp(self):
        self.holding = Holding(primary_redis=test_redis,
                               annotates=set(["bibframe:Instance:1"]))
        setattr(self.holding,'callno-local','Video 6716')
        setattr(self.holding,'callno-lcc','C1.D11')
        self.holding.save()
        self.existing_redis_key = "bibframe:Instance:{0}".format(test_redis.incr('global bibframe:Instance'))
        test_redis.hset(self.existing_redis_key,
                        'created_on',
                        datetime.datetime.utcnow().isoformat())
        self.instance = Instance(primary_redis=test_redis,
                                 redis_key=self.existing_redis_key,
                                 associatedAgent={'rda:publisher':set(['bibframe:Organization:1'])},
                                 hasAnnotation=set([self.holding.redis_key,]),
                                 instanceOf="bibframe:Work:1")
        self.new_holding = Holding(primary_redis=test_redis)
        setattr(self.new_holding,"callno-sudoc",'HD1695.C7C55 2007')
        self.new_holding.save()
        self.new_instance = Instance(primary_redis=test_redis,
                                     associatedAgent={'rda:publisher':set(['bibframe:Organization:2'])},
                                     hasAnnotation=set([self.new_holding.redis_key,]),
                                     instanceOf="bibframe:Work:2")
        setattr(self.new_instance,'system-number','b1762075')
        self.new_instance.save()
        setattr(self.new_holding,'annotates',set([self.new_instance.redis_key,]))
        self.new_holding.save()

    def test_ils_bib_number(self):
        self.assertEquals(getattr(self.new_instance,'system-number'),
                          test_redis.hget(self.new_instance.redis_key,
                                          "system-number"))

    def test_init(self):
        self.assert_(self.new_instance.primary_redis)
        self.assertEquals(self.new_instance.redis_key,
                          'bibframe:Instance:2')
        self.assert_(self.instance.primary_redis)
        self.assertEquals(self.instance.redis_key,
                          "bibframe:Instance:1")

    def test_lccn_callnumber(self):
        self.assertEquals(list(self.instance.hasAnnotation)[0],
                          self.holding.redis_key)
        self.assertEquals(getattr(self.holding,'callno-lcc'),
                          test_redis.hget(self.holding.redis_key,
                                          'callno-lcc'))
        self.assertEquals(test_redis.hget(list(self.instance.hasAnnotation)[0],
                                          'callno-lcc'),
                          "C1.D11")
        

    def test_local_callnumber(self):
        self.assertEquals(getattr(self.holding,'callno-local'),
                          "Video 6716")
        self.assertEquals(getattr(self.holding,'callno-local'),
                          test_redis.hget(self.holding.redis_key,
                                          'callno-local'))
        self.assertEquals(self.holding.redis_key,
                          list(self.instance.hasAnnotation)[0])
                          

    def test_publisher(self):
        self.assertEquals(list(self.new_instance.associatedAgent['rda:publisher'])[0],
                          'bibframe:Organization:2')
        self.assertEquals(list(self.instance.associatedAgent['rda:publisher'])[0],
                          'bibframe:Organization:1')

    def test_sudoc_callnumber(self):
        self.assertEquals(list(self.new_instance.hasAnnotation)[0],
                          self.new_holding.redis_key)
        self.assertEquals(getattr(self.new_holding,"callno-sudoc"),
                          test_redis.hget(self.new_holding.redis_key,
                                          "callno-sudoc"))
        

    def tearDown(self):
        test_redis.flushdb()

class TestCreativeWork(TestCase):

    def setUp(self):
        # Test work w/o Redis key (new Work)
        self.new_creative_work = Work(primary_redis=test_redis,
                                      associatedAgent={'rda:isCreatedBy':set(["bibframe:Person:1"])},
                                      languageOfWork="eng",
                                      note=["This is a note for a new creative work",])
        setattr(self.new_creative_work,'rda:dateOfWork',2012)

        self.new_creative_work.save()
        # Tests work w/pre-existing Redis 
	self.existing_key = 'bibframe:Work:2'
        test_redis.hset(self.existing_key,'created','2013-01-07')
        test_redis.hset(self.existing_key,'rda:dateOfWork',1999)
        self.creative_work = Work(primary_redis=test_redis,
                                  redis_key=self.existing_key,
                                  associatedAgent={'rda:isCreatedBy':set(["bibframe:Organization:1"])})
        self.creative_work.save()


    def test_init_(self):
        self.assert_(self.new_creative_work.primary_redis)
        self.assertEquals(self.new_creative_work.redis_key,
                          'bibframe:Work:1')
        self.assert_(self.creative_work.primary_redis)
        self.assertEquals(self.creative_work.redis_key,
                          "bibframe:Work:2")

    def test_dateOfWork(self):
        self.assertEquals(str(getattr(self.new_creative_work,'rda:dateOfWork')),
                          test_redis.hget(self.new_creative_work.redis_key,
                                          "rda:dateOfWork"))
        self.assertEquals(getattr(self.creative_work,'rda:dateOfWork'),
                          test_redis.hget(self.creative_work.redis_key,
                                          'rda:dateOfWork'))

    def test_isCreatedBy(self):
        self.assertEquals(list(self.new_creative_work.associatedAgent['rda:isCreatedBy'])[0],
		          'bibframe:Person:1')
        self.assertEquals(list(self.creative_work.associatedAgent['rda:isCreatedBy'])[0],
                          'bibframe:Organization:1')


    def tearDown(self):
        test_redis.flushdb()


class TestLibraryHolding(TestCase):

    def setUp(self):
        self.new_holding = Holding(primary_redis=test_redis,
                                   annotates='bibframe:Instance:1')
        setattr(self.new_holding,'callno-lcc','PS3602.E267 M38 2008')
        setattr(self.new_holding,'callno-udc','631.321:631.411.3')
        setattr(self.new_holding,'callno-ddc','388/.0919')
        self.new_holding.save()

    def test_init(self):
        self.assert_(self.new_holding.redis_key is not None)

    def test_annotates(self):
        self.assertEquals(self.new_holding.annotates,
                          'bibframe:Instance:1')
  
    def test_callno_ddc(self):
        self.assertEquals(self.new_holding.feature('callno-ddc'),
                          '388/.0919')

    def test_callno_lcc(self):
        self.assertEquals(self.new_holding.feature('callno-lcc'),
                          'PS3602.E267 M38 2008')

    def test_udc(self):
        self.assertEquals(self.new_holding.feature('callno-udc'),
                          '631.321:631.411.3')



    def tearDown(self):
        test_redis.flushdb()

class TestTitleInfo(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        test_redis.flushdb()


"""
Tries to import all classifiers and ingester tests
"""
from bibframe.classifiers.tests import TestWorkClassifier
from bibframe.ingesters.test_ProjectGutenbergRDF import TestProjectGutenbergIngester
from bibframe.ingesters.test_MODS import TestMODSforOralHistoryIngester
from bibframe.ingesters.test_Ingester import TestPersonalNameParser
from bibframe.ingesters.test_MARC import *
