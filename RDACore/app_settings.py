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
