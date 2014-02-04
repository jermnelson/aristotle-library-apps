"""
 mod:`urls` Title Search App URL routing
"""
__author__ = "Jeremy Nelson"

try:
    from django.conf.urls.defaults import *
except ImportError:
    from django.conf.urls import *

urlpatterns = patterns('person_authority.views',
    url(r"$^","app",name="person-authority-default"),
    url(r"search$","search",name="person-authority-search-json")
)
