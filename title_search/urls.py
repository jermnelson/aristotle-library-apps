"""
 mod:`urls` Title Search App URL routing
"""
__author__ = "Jeremy Nelson"

try:
    from django.conf.urls.defaults import *
except ImportError:
    from django.conf.urls import *

urlpatterns = patterns('title_search.views',
    url(r"$^","app",name="title-search-default"),
    url(r"search$","search",name="title-search-json"),
)
