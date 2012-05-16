"""
 :mod:`views` Orders App Views
"""
__author__ = "Jeremy Nelson"

from datetime import datetime
from django.views.generic.simple import direct_to_template
from app_settings import APP
from settings import INSTITUTION


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
   return direct_to_template(request,
                             'orders/app.html',
                             {'app':APP,
                              'institution':INSTITUTION,
                              'date':datetime.today()})


