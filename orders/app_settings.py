try:
    from aristotle.settings import REDIS_PASSWORD,REDIS_PRODUCTIVITY_HOST,REDIS_PRODUCTIVITY_PORT
    REDIS_HOST = REDIS_PRODUCTIVITY_HOST
    REDIS_PORT = REDIS_PRODUCTIVITY_PORT
except ImportError:
##    REDIS_HOST = '172.25.1.108'
##    REDIS_PORT = 6379
##    REDIS_PASSWORD = None
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    REDIS_PASSWORD = None
    

APP = {'current_view': {'title':'Orders App'},
       'description': 'The Order App is an administrative app for managing the Library orders for the collection',
       'icon_url':'budget.png',
       'productivity':True,
       'url':'orders/',
}
