"""
 mod:`url` Article Search Application URL routing
"""
__author__ = 'Gautam Webb'
import article_search.views
from django.conf.urls.defaults import *

urlpatterns = patterns('article_search.views',
    url(r"^$","default",name='article_search-app-default'),
    url(r"^widget$","widget"),
)
                       
