"""
 :mod:`views` Orders App Views
"""
__author__ = "Jeremy Nelson"

import redis_helpers
from django.http import HttpResponse
from datetime import datetime,timedelta
from django.views.generic.simple import direct_to_template
from app_settings import APP
from aristotle.settings import INSTITUTION


def browse_month(request,year,month):
   """
   Displays a month's activity
   """
   date = datetime(int(year),int(month),1)
   last_date = date + timedelta(weeks=4)
   orders = []
   order_keys = redis_helpers.redis_server.zrangebyscore('orders',
                                                         date.toordinal(),
                                                         last_date.toordinal())
   
   return direct_to_template(request,
                             'orders/month.html',
                             {'app':APP,
                              'end_date':last_date,
                              'institution':INSTITUTION,
                              'date':date,
                              'orders':order_keys})

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

def pcard_display(request,counter):
    """
    Displays a single pcard display

    :param request: Web request
    :param request: counter
    """
    pcard_key = 'pcard:%s' % counter
    pcard = redis_helpers.get_entity(redis_key=pcard_key)
    return direct_to_template(request,
                             'orders/app.html',
                             {'app':APP,
                              'entity':pcard,
                              'entity_type':'PCARD',
                              'institution':INSTITUTION,
                              'date':datetime.today()})


def invoice_display(request,counter):
    invoice_key = 'invoice:%s' % counter
    invoice = redis_helpers.get_entity(redis_key=invoice_key)
    return direct_to_template(request,
                             'orders/app.html',
                             {'app':APP,
                              'entity':invoice,
                              'entity_type':'Invoice',
                              'institution':INSTITUTION,
                              'date':datetime.today()})

def voucher_display(request,counter):
    voucher_key = 'voucher:%s' % counter
    voucher = redis_helpers.get_voucher(voucher_key)
    return direct_to_template(request,
                             'orders/voucher.html',
                             {'app':APP,
                              'voucher':voucher,
                              'institution':INSTITUTION,
                              'date':datetime.today()})


