import redis
try:
    import aristotle.settings as settings
    REDIS_SERVER = TITLE_REDIS

except:
    # Setup for non-Django local development
    REDIS_SERVER = redis.StrictRedis(host='127.0.0.1',
                                     port=6384)
    

APP = {'current_view': {'title':'Title Search'},
       'description': 'The Title Search App provides a typeahead Title search and a browe nearby titles',
       'icon_url':'title-search.png',
       'url':'title_search/'}


