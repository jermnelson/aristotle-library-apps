"""
 mod:test_bayes

"""
__name__ = "Jeremy Nelson"
import datetime
import os
import pymarc
import unittest
from bibframe.classifiers.naive_bayes import WorkClassifier
from aristotle.settings import TEST_REDIS, PROJECT_HOME

class TestNaiveBayesWorkClassifier(unittest.TestCase):
    "Tests NaiveByes WorkClassifer class"

    def setUp(self):
        self.classifier = WorkClassifer(annotation_ds=TEST_REDIS,
                                        authority_ds=TEST_REDIS,
                                        creative_work_ds=TEST_REDIS,
                                        instance_ds=TEST_REDIS)


    def tearDown(self):
        TEST_REDIS.flushdb()
    
