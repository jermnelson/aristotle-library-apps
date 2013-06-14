"""
 Unit tests for BIBFRAME Simple Fuzzy Classifier
"""
__author__ = "Jeremy Nelson"

import redis
import simple_fuzzy
import unittest
from bibframe.models import Book, TitleEntity
from title_search.redis_helpers import index_title
from aristotle.settings import TEST_REDIS

class TestWorkClassifier(unittest.TestCase):

    def setUp(self):
        self.title_entity = TitleEntity(redis_datastore = TEST_REDIS,
                                        label='Pride and Prejudice',
                                        titleValue='Pride and Prejudice')
        self.title_entity.save()
        index_title(self.title_entity, TEST_REDIS)
        self.work = Book(redis_datastore=TEST_REDIS,
                         associatedAgent=set(["bf:Person:1"]),
                         title=self.title_entity.redis_key)
        setattr(self.work, 'rda:isCreatedBy', 'bf:Person:1')
        self.work.save()
        TEST_REDIS.sadd(
            "{0}:relatedResources".format(self.title_entity.redis_key),
            self.work.redis_key)

    def test_init(self):
        entity_info = {'title': 'Pride and Prejudice',
                       'rda:isCreatedBy': set(['bf:Person:1'])}
        classifier = simple_fuzzy.WorkClassifier(redis_datastore = TEST_REDIS,
                                                 entity_info = entity_info,
                                                 work_class=Book)
        self.assert_(classifier is not None)
        self.assert_(classifier.strict is True)
        self.assert_(classifier.creative_work is None)
        self.assertEquals(classifier.entity_info,
                          entity_info)


    def test_exact_match(self):
        entity_info = {'rda:isCreatedBy': set(['bf:Person:1']),
                       'title': self.title_entity.redis_key,}
        classifier = simple_fuzzy.WorkClassifier(redis_datastore = TEST_REDIS,
                                                 entity_info = entity_info,
                                                 work_class=Book)
        classifier.classify()
        self.assertEquals(classifier.creative_work.redis_key,
                          self.work.redis_key)

    def tearDown(self):
        TEST_REDIS.flushdb()
##        pass
        
                        
        
