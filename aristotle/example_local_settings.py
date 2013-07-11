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
INSTITUTION = {'background-logo': 'cc-logo-gold.png',
               'name': 'Tutt Library',
               'logo': 'tutt-library-spring.png',
               'url':'http://www.coloradocollege.edu/library/xindex.dot'}
# Creates RDA Redis Instances for use by the Aristotle Library Apps
#
if LOCAL is True:
    REDIS_MASTER_HOST = '127.0.0.1'
else:
    REDIS_MASTER_HOST = '127.0.0.1'

CUSTOM_AUTHENTICATION_BACKENDS = []
# Runs all Redis RDA instances on a single server
if SINGLE_SERVER is True:
    REDIS_ANNOTATION_HOST = REDIS_MASTER_HOST
    REDIS_AUTHORITY_HOST = REDIS_MASTER_HOST
    REDIS_CREATIVE_WORK_HOST = REDIS_MASTER_HOST
    REDIS_INSTANCE_HOST = REDIS_MASTER_HOST
    REDIS_CORPORATEBODY_HOST = REDIS_MASTER_HOST
    REDIS_EXPRESSION_HOST = REDIS_MASTER_HOST
    REDIS_ITEM_HOST = REDIS_MASTER_HOST
    REDIS_MANIFESTION_HOST = REDIS_MASTER_HOST
    REDIS_PERSON_HOST = REDIS_MASTER_HOST
    REDIS_SUBJECT_HOST = REDIS_MASTER_HOST
    REDIS_TITLE_HOST = REDIS_MASTER_HOST
## Uncomment out next line to run on multiple servers after SINGLE_SERVER = False
## else:
##    REDIS_CORPORATEBODY_HOST = ''
##    REDIS_EXPRESSION_HOST = ''
##    REDIS_ITEM_HOST = ''
##    REDIS_MANIFESTION_HOST = ''
##    REDIS_PERSON_HOST = ''
##    REDIS_SUBJECT_HOST = ''
##    REDIS_TITLE_HOST = ''
##    REDIS_WORK_HOST = ''

ANNOTATION_REDIS = redis.StrictRedis(host=REDIS_ANNOTATION_HOST)
AUTHORITY_REDIS = redis.StrictRedis(host=REDIS_AUTHORITY_HOST)
CREATIVE_WORK_REDIS = redis.StrictRedis(host=REDIS_CREATIVE_WORK_HOST)
INSTANCE_REDIS = redis.StrictRedis(host=REDIS_INSTANCE_HOST)
OPERATIONAL_REDIS = redis.StrictRedis(host=REDIS_MASTER_HOST)
TEST_REDIS = redis.StrictRedis(host=REDIS_MASTER_HOST)
