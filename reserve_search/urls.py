"""
 mod:`url` Reserve Search Application URL routing
"""
__author__ = 'Jon Driscoll & Gautam Webb'
import reserve_search.views
from django.conf.urls.defaults import *

urlpatterns = patterns('reserve_search.views',
    url(r"^$","default",name='reserve_search-app-default'),
    url(r"^widget$","widget"),
    url(r"^dotCMS$","dotCMS"),
)                       
