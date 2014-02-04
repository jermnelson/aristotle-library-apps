"""
 mod:`url` Portfolio Application URL routing
"""
__author__ = 'Jeremy Nelson'
import portfolio.views
try:
    from django.conf.urls.defaults import *
except ImportError:
    from django.conf.urls import *

urlpatterns = patterns('portfolio.views',
    url(r"^$","default",name='portfolio-default'),
)

