import redis
LOCAL = True
SINGLE_SERVER = True

SECRET_KEY = 'CREATE YOUR OWN RANDOM KEY'

DISCOVERY_RECORD_URL = ''


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

# Runs all Redis RDA instances on a single server
if SINGLE_SERVER is True:
    REDIS_CORPORATEBODY_HOST = REDIS_MASTER_HOST
    REDIS_EXPRESSION_HOST = REDIS_MASTER_HOST
    REDIS_ITEM_HOST = REDIS_MASTER_HOST
    REDIS_MANIFESTION_HOST = REDIS_MASTER_HOST
    REDIS_PERSON_HOST = REDIS_MASTER_HOST
    REDIS_SUBJECT_HOST = REDIS_MASTER_HOST
    REDIS_TITLE_HOST = REDIS_MASTER_HOST
    REDIS_WORK_HOST = REDIS_MASTER_HOST
## Uncomment out enxt line to run on multiple servers after SINGLE_SERVER = False
## else:
##    REDIS_CORPORATEBODY_HOST = ''
##    REDIS_EXPRESSION_HOST = ''
##    REDIS_ITEM_HOST = ''
##    REDIS_MANIFESTION_HOST = ''
##    REDIS_PERSON_HOST = ''
##    REDIS_SUBJECT_HOST = ''
##    REDIS_TITLE_HOST = ''
##    REDIS_WORK_HOST = ''
CORPORATEBODY_REDIS = redis.StrictRedis(host=REDIS_CORPORATEBODY_HOST,
                                        port=6387)
EXPRESSION_REDIS = redis.StrictRedis(host=REDIS_EXPRESSION_HOST,
                                     port=6381)
ITEM_REDIS = redis.StrictRedis(host=REDIS_ITEM_HOST,
                               port=6383)
MANIFESTION_REDIS = redis.StrictRedis(host=REDIS_MANIFESTION_HOST,
                                      port=6382)
OPERATIONAL_REDIS = redis.StrictRedis(host=REDIS_MASTER_HOST,
                                      port=6379)
PERSON_REDIS = redis.StrictRedis(host=REDIS_PERSON_HOST,
                                 port=6385)
SUBJECT_REDIS = redis.StrictRedis(host=REDIS_SUBJECT_HOST,
                                  port=6385)
TITLE_REDIS = redis.StrictRedis(host=REDIS_TITLE_HOST,
                                port=6384)
WORK_REDIS = redis.StrictRedis(host=REDIS_WORK_HOST,
                               port=6380)

