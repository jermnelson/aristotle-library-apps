"""
 :mod:`url` Order App URL routing
"""
__author__ = 'Jeremy Nelson'
import orders.views
from django.conf.urls.defaults import *

urlpatterns = patterns('orders.views',
    url(r"^$","default",name='orders-app-default'),
    url(r"(?P<year>\d+)/(?P<month>\d+)/","browse_month",name='orders-app-year-month')
#    url(r"browse$","browse",name="invoices-app-browse"),
)
                       
