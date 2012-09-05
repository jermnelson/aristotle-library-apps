import redis
APP = {'current_view': {'title':'Title Search'},
       'description': 'The Title Search App provides a typeahead Title search and a browe nearby titles',
       'icon_url':'call_number_search.png',
       'url':'title_search/'}

try:
    import aristotle.settings as settings
    REDIS_HOST = settings.REDIS_MASTER_HOST
    REDIS_PORT = settings.REDIS_MASTER_PORT
except:
    # Setup for local development
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
REDIS_SERVER = redis.StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
