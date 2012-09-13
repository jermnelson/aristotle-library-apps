import redis
import aristotle.settings as settings

APP = {'current_view': {'title':'RDA Core'},
       'description': 'The RDA Core App a Discovery and Access App for searching and browsing bibliographic records.',
       'icon_url':'rdaCore.png',
       'url':'RDAcore/'}
       

FACETS = [{'body_id':'access-facet',
           'name':"Access"},
          {'body_id':'format-facet',
           'name':"Format"},
          {"body_id":'topics-facet',
           'name':'Topics'}]

WORK_REDIS = redis.StrictRedis(host=settings.REDIS_WORK_HOST,
                               port=settings.REDIS_WORK_PORT)

EXPRESSION_REDIS = redis.StrictRedis(host=settings.REDIS_EXPRESSION_HOST,
                                     port=settings.REDIS_EXPRESSION_PORT)

MANIFESTATION_REDIS = redis.StrictRedis(host=settings.REDIS_MANIFESTATION_HOST,
                                        port=settings.REDIS_MANIFESTATION_PORT)

ITEM_REDIS = redis.StrictRedis(host=settings.REDIS_ITEM_HOST,
                               port=settings.REDIS_ITEM_PORT)

TITLE_REDIS = redis.StrictRedis(host=settings.REDIS_TITLE_HOST,
                                port=settings.REDIS_TITLE_PORT)

PERSON_REDIS = redis.StrictRedis(host=settings.REDIS_PERSON_HOST,
                                 port=settings.REDIS_PERSON_PORT)
