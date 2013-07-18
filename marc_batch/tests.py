"""
 :mod:`tests` Unit Tests for MARC Batch App functionality 
"""
__author__ = "Jeremy Nelson"
import redis,pymarc,datetime
import json
from django.test import TestCase
from aristotle.settings import TEST_REDIS

