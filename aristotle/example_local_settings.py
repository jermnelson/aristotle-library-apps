__author__ = "Jeremy Nelson"
import redis
# The minimum Aristotle Library Apps Environment is made up of three active apps
ACTIVE_APPS = ['bibframe',
               'discovery',
               'portfolio']

# Setting both LOCAL and SINGLE_SERVER to True for minimum installation
LOCAL = True
SINGLE_SERVER = True

# Create a secret key for use by Django
SECRET_KEY = ''

# INSTITUTION settings
INSTITUTION = {'background-logo': None,
               'name': 'Aristotle Library Apps',
               'logo': 'aristole-library-apps.png',
               'url':''}
# Settings to connect to BIBFRAME instance, setting all ports to 
# the same Redis instance
REDIS_HOST = '0.0.0.0'
ANNOTATION_REDIS = redis.StrictRedis(host=REDIS_HOST,
                                     port=6379)
AUTHORITY_REDIS = redis.StrictRedis(host=REDIS_HOST,
                                    port=6379)
INSTANCE_REDIS = redis.StrictRedis(host=REDIS_HOST,
                                   port=6379)
OPERATIONAL_REDIS = redis.StrictRedis(host=REDIS_HOST,port=6379)
TEST_REDIS = redis.StrictRedis(host=REDIS_HOST,port=6379)
CREATIVE_WORK_REDIS = redis.StrictRedis(host=REDIS_HOST,
                                        port=6379)
