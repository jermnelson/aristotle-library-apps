"""
 mod:`urls` RDA Core URL routing
"""
__author__ = 'Jeremy Nelson'
import RDACore.views
from django.conf.urls.defaults import *

urlpatterns = patterns('RDACore.views',
    url(r"^$","default",name='rda-core-home'),
)
