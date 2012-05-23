"""
 mod:`url` Portfolio Application URL routing
"""
__author__ = 'Jeremy Nelson'
import portfolio.views
from django.conf.urls.defaults import *

urlpatterns = patterns('portfolio.views',
    url(r"^$","default",name='portfolio-default'),
)
                       
