"""
 :mod:`views` Orders App Views
"""
__author__ = "Jeremy Nelson"

import redis_helpers
from datetime import datetime
from django.views.generic.simple import direct_to_template
from app_settings import APP
from aristotle.settings import INSTITUTION


def browse_month(request,year,month):
   """
   Displays a month's activity
   """
   date = datetime(int(year),int(month),1)
   return direct_to_template(request,
                             'orders/app.html',
                             {'app':APP,
                              'institution':INSTITUTION,
                              'date':date})

def default(request):
   """
   default is the standard view for the orders app

   :param request: Web request
   """
   entity_key = redis_helpers.redis_server.zrange('orders',-1,-1)
   entity_type = entity_key[0].split(":")[0].upper()
   entity = redis_helpers.get_entity(redis_key=entity_key[0])
   return direct_to_template(request,
                             'orders/app.html',
                             {'app':APP,
                              'entity':entity,
                              'entity_type':entity_type,
                              'institution':INSTITUTION,
                              'date':datetime.today()})


