"""
 :mod:`redis_helpers` RDA Core Helper Utilities
"""
import pymarc,redis,re
import logging,sys
from app_settings import APP,SEED_RECORD_ID
try:
    import aristotle.settings as settings
    REDIS_HOST = settings.REDIS_ACCESS_HOST
    REDIS_PORT = settings.REDIS_ACCESS_PORT
    TEST_DB = settings.REDIS_TEST
    volatile_redis = redis.StrictRedis(host=settings.REDIS_PRODUCTIVITY_HOST,
                                       port=settings.REDIS_PRODUCTIVITY_PORT)

except ImportError:
    # Setup for local development
    REDIS_HOST = '172.25.1.108'
##    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    TEST_DB = 3
    volatile_redis = None
    

# RDA Core should reside on primary DB of 0
redis_server = redis.StrictRedis(host=REDIS_HOST,
                                 port=REDIS_PORT)    


    

def search(query):
    set_rank = redis_server.zrank('call-number-sorted-search-set',query)
    output = {'result':[]}
    for row in redis_server.zrange('call-number-sorted-search-set',set_rank,-1):
        if row[-1] == "*":
            call_number = row[:-1]
            record = get_record(call_number)
            output['result'].append(call_number)
            output['record'] = record
            output['discovery_url'] = '%s%s' % (settings.DISCOVERY_RECORD_URL,
                                                record['bib_number'])
            return output
        else:
            output['result'].append(row)
    return output

    
    
    
