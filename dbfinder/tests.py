"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import redis_helpers
from bibframe.models import Instance, Person, Work
from django.test import TestCase
from aristotle.settings import TEST_REDIS

test_redis = TEST_REDIS

class GetDatabaseTest(TestCase):

    def setUp(self):
        new_database = Work(primary_redis=test_redis,
                            description="A new database of Art and Artists",
                            title={"rda:preferredTitleOfWork":"Art and Artists",
                                   "rda:varientTitle":["Art's Aritists"]})

        new_database.save()
        self.db_redis_key = new_database.redis_key
        new_db_instance = Instance(primary_redis=test_redis,
                                   instanceOf=new_database.redis_key,
                                   uri="http://ArtAndArtists.html")
        new_db_instance.save()
        setattr(new_database,"bibframe:Instances",new_db_instance.redis_key)
        new_database.save()

    def test_get_database(self):
        result = redis_helpers.__get_database__(self.db_redis_key,
                                                test_redis,
                                                test_redis)
        self.assertEquals(result.get('description'),
                          "A new database of Art and Artists")
        self.assertEquals(result.get('title'),
                          "Art and Artists")

    def tearDown(self):
        test_redis.flushdb()

class GetDatabasesTest(TestCase):

    def setUp(self):
        db_1 = Work(primary_redis=test_redis,
                    description="Chemistry Abstracts is a citation database focusing on Chemistry peer-reviewed articles",
                    title="Chemistry Abstracts",
                    uri="http://chemabstracts.com")
        db_1.save()
        test_redis.sadd("dbfinder:alpha:C",db_1.redis_key)
        test_redis.sadd("dbfinder:alphas","dbfinder:alpha:C")
        test_redis.sadd("dbfinder:subjects:Chemistry",db_1.redis_key)
        test_redis.sadd("dbfinder:subjects","dbfinder:subjects:Chemistry")
        db_2 = Work(primary_redis=test_redis,
                    description="Philosophy and Religion Today contains historical and current articles related to the Philosophy of Religion",
                    title="Philosophy and Religion",
                    uri="http://www.philosophy_religion.net")
        db_2.save()
        test_redis.sadd("dbfinder:alpha:P",db_2.redis_key)
        test_redis.sadd("dbfinder:alphas","dbfinder:alpha:P")
        test_redis.sadd("dbfinder:subjects:Philosophy",db_2.redis_key)
        test_redis.sadd("dbfinder:subjects","dbfinder:subjects:Philosophy")

    def test_raises_exception_None_all(self):
        self.assertRaises(ValueError,
                          redis_helpers.get_databases, 
                          None, # letter 
                          None, # subject
                          test_redis, 
                          test_redis, 
                          test_redis)

    def test_raises_exception_both_values(self):
        self.assertRaises(ValueError,
                          redis_helpers.get_databases, 
                          'A', # letter 
                          "Art", # subject
                          test_redis, 
                          test_redis, 
                          test_redis)
    
    def test_get_letter(self):
         databases = redis_helpers.get_databases("P",
                                                 None,
                                                 test_redis,
                                                 test_redis,
                                                 test_redis)
         self.assertEquals(len(databases),1)


    def tearDown(self):
        test_redis.flushdb()

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
