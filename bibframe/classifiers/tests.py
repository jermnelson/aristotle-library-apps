"""
 Unit tests for BIBFRAME Simple Fuzzy Classifier
"""
__author__ = "Jeremy Nelson"

import redis
import simple_fuzzy
import unittest

from bibframe.models import Work

try:
    from aristotle.settings import TEST_REDIS
except ImportError, e:
    TEST_REDIS = redis.StrictRedis(host="192.168.64.143",
                                   port=6385)

class TestWorkClassifier(unittest.TestCase):

    def setUp(self):
        self.work = Work(primary_redis=TEST_REDIS,
                         associatedAgent=set(["bibframe:Person:1"]),
                         title={'rda:preferredTitleForTheWork':'Pride and Prejudice'})
        setattr(self.work, 'rda:isCreatedBy', 'bibframe:Person:1')
        self.work.save()
        

    def test_init(self):
        entity_info = {'title': {'rda:preferredTitleForTheWork': 'Pride and Prejudice'},
                       'rda:isCreatedBy': set(['bibframe:Person:1'])}
        classifier = simple_fuzzy.WorkClassifier(annotation_ds = TEST_REDIS,
                                                 authority_ds = TEST_REDIS,
                                                 creative_work_ds = TEST_REDIS,
                                                 instance_ds = TEST_REDIS,
                                                 entity_info = entity_info)
        self.assert_(classifier is not None)
        self.assert_(classifier.strict is True)
        


    def test_exact_match(self):
        entity_info = {'title': {'rda:preferredTitleForTheWork': 'Pride and Prejudice'},
                       'rda:isCreatedBy': set(['bibframe:Person:1'])}
        classifier = simple_fuzzy.WorkClassifier(annotation_ds = TEST_REDIS,
                                                 authority_ds = TEST_REDIS,
                                                 creative_work_ds = TEST_REDIS,
                                                 instance_ds = TEST_REDIS,
                                                 entity_info = entity_info)
        classifier.classify()
        self.assertEquals(classifier.creative_work.redis_key,
                          self.work.redis_key)

    def tearDown(self):
        TEST_REDIS.flushdb()
                        
        
