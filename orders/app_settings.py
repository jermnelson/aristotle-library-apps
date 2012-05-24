try:
    from aristotle.settings import DOTCLOUD,REDIS_HOST,REDIS_PASSWORD
except:
    DOTCLOUD = False

APP = {'current_view': {'title':'Orders App'},
       'description': 'The Order App is an administrative productivity app for managing the Library orders for the collection',
       'icon_url':'budget.png',
       'productivity':True,
       'url':'orders/',
}
if DOTCLOUD is True:
    REDIS_HOST = settings.REDIS_PRODUCTIVITY_HOST
    REDIS_PORT = settings.REDIS_PRODUCTIVITY_PORT
    REDIS_PASSWORD = settings.REDIS_PASSWORD
else:
    REDIS_HOST = '0.0.0.0'
    REDIS_PORT = 6379
    REDIS_PASSWORD = None
