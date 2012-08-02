"""
 :mod:`redis_helpers` RDA Core Helper Utilities
"""
import pymarc,redis,re
import logging,sys
from app_settings import APP
try:
    raise ImportError
##    import aristotle.settings as settings
##    REDIS_HOST = settings.REDIS_ACCESS_HOST
##    REDIS_PORT = settings.REDIS_ACCESS_PORT
##    TEST_DB = settings.REDIS_TEST
##    volatile_redis = redis.StrictRedis(host=settings.REDIS_PRODUCTIVITY_HOST,
##                                       port=settings.REDIS_PRODUCTIVITY_PORT)

except ImportError:
    # Setup for local development
##    REDIS_HOST = '172.25.1.108'
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    TEST_DB = 3
    volatile_redis = None
    

# RDA Core should reside on primary DB of 0
redis_server = redis.StrictRedis(host=REDIS_HOST,
                                 port=REDIS_PORT)    


    
def get_facets(entity_name):
    facets = {"label":entity_name,
              "count":redis_server.get("global:rdaCore:{0}".format(entity_name))}
    return facets

    
    
    
