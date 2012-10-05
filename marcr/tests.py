"""
 :mod:`tests` - Unit tests for the Bibliographic Framework App
"""
import redis
from django.test import TestCase
from app_helpers import *
try:
    from aristotle.settings import TEST_REDIS
except ImportError, e:
    TEST_REDIS = redis.StrictRedis(host="192.168.64.139",port=6385)
test_redis = TEST_REDIS

class BibFrameworkModelTest(TestCase):

    def setUp(self):
        self.base_bibframe = BibFrameworkModel(redis=test_redis,
                                               redis_key='base-bib-framework:1')
        self.empty_base_bibframe = BibFrameworkModel()
        
    
    def test_init(self):
        """
        Tests initalization of base class
        """
        self.assert_(self.base_bibframe.redis is not None)
        self.assertEquals(self.base_bibframe.redis_key,
                          'base-bib-framework:1')
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
                                        redis_key="Authority:1")

    def test_init(self):
        self.assert_(self.new_base_authority.redis is not None)
        self.assertEquals(self.base_authority.redis_key,
                          "Authority:1")

    def tearDown(self):
        test_redis.flushdb()

class PersonAuthorityTest(TestCase):

    def setUp(self):
        self.person = Person(redis=test_redis,
                             attributes={'rda:dateOfBirth':'1962-04-21',
                                         'rda:dateOfDeath':'2008-09-12',
                                         'rda:gender':'male',
                                         'rda:Name':'Wallace, David Foster',
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
                          test_redis.hget("{0}{1}".format(self.person.redis_key,
                                                          'rda:identifierFor'),
                                          'loc'))

    def test_name(self):
        self.assertEquals(self.person.attributes['rda:Name'],
                          test_redis.hget(self.person.redis_key,
                                          'rda:Name'))

    

    
    def test_save(self):
        self.assertEquals(self.person.redis_key,
                          "Authority:Person:1")

    def tearDown(self):
        test_redis.flushdb()

class InstanceTest(TestCase):

    def setUp(self):
        existing_attributes = {'rda:publisher':'Authority:CorporateBody:1'}
        new_attributes = {'rda:publisher':'Authority:CorporateBody:2'}
        self.instance = Instance(redis=test_redis,
                                 redis_key="Instance:2",
                                 attributes=existing_attributes)        
        self.new_instance = Instance(redis=test_redis,
                                     attributes=new_attributes)
        

    def test_init(self):
        self.assert_(self.new_instance.redis)
        self.assert_(self.new_instance.redis_key is None)
        self.assert_(self.instance.redis)
        self.assertEquals(self.instance.redis_key,
                          "Instance:2")

    def test_publisher(self):
        self.new_instance.save()
        self.instance.save()
        self.assertEquals(self.new_instance.attributes['rda:publisher'],
                          'Authority:CorporateBody:2')
        self.assertEquals(self.instance.attributes['rda:publisher'],
                          'Authority:CorporateBody:1')
                

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
                         redis_key="Work:2",
                         attributes=existing_attributes)

    def test_init_(self):
        self.assert_(self.new_work.redis)
        self.assert_(self.new_work.redis_key is None)
        self.assert_(self.work.redis)
        self.assertEquals(self.work.redis_key,
                          "Work:2")

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
        self.assertEquals(self.new_work.redis_key,"Work:1")
        self.assert_(test_redis.hget(self.work.redis_key,
                                     'created'))
        self.assertEquals(self.new_work.attributes['created'],
                          test_redis.hget(self.work.redis_key,
                                          'created'))
        self.assert_(test_redis.exists(self.work.redis_key))
        

    
                                          

    def tearDown(self):
        test_redis.flushdb()
        
        
                                   
        
        
