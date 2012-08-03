import redis
APP = {'current_view': {'title':'Call Number'},
       'description': 'The Call Number Search App provides a typeahead Call Number search and a browse shelf widget. ',
       'icon_url':'call_number_search.png',
       'url':'call_number/'}

SEED_RECORD_ID = 'rdaCore:Expression:280'
try:
    import aristotle.settings as settings
    REDIS_HOST = settings.REDIS_MASTER_HOST
    REDIS_PORT = settings.REDIS_MASTER_PORT
except:
    # Setup for local development
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
REDIS_SERVER = redis.StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
