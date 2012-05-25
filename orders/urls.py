"""
 :mod:`url` Order App URL routing
"""
__author__ = 'Jeremy Nelson'
import orders.views
from django.conf.urls.defaults import *

urlpatterns = patterns('orders.views',
    url(r"^$","default",name='orders-app-default'),
    url(r"^invoice\:(\d+)","invoice_display",name="orders-invoice-display"),
    url(r"^pcard\:(\d+)","pcard_display",name='orders-pcard-display'),
    url(r"^voucher\:(\d+)","voucher_display",name='orders-voucher-display'),
    url(r"(?P<year>\d+)/(?P<month>\d+)/","browse_month",name='orders-app-year-month')
##    url(r"^invoices$","invoices"),
##    url(r"^pcards$","pcards"),
#    url(r"browse$","browse",name="invoices-app-browse"),
)
                       
