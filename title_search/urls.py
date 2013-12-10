"""
 mod:`urls` Title Search App URL routing
"""
__author__ = "Jeremy Nelson"

from django.conf.urls import *

urlpatterns = patterns('title_search.views',
    url(r"$^","app",name="title-search-default"),
    url(r"search$","search",name="title-search-json"),
)
