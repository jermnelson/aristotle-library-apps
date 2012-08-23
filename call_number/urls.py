"""
 mod:`url` Call Number Application URL routing
"""
__author__ = 'Jeremy Nelson'
import call_number.views
from django.conf.urls.defaults import *

urlpatterns = patterns('call_number.views',
    url(r"^$","app",name='call-number-default'),
    url(r"info$","default"),
    url(r"json/browse$",'browse'),
    url(r"json/search$","typeahead_search"),
    url(r"json/term_search","term_search"),
    url(r'widget$','widget'),
)
                       
