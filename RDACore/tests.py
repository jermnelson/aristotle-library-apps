"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import redis
from django.test import TestCase
from redis_helpers import *
import pymarc

test_ds = redis.StrictRedis(db=TEST_DB)



    
        
