"""
 mod:`urls` Title Search App URL routing
"""
__author__ = "Jeremy Nelson"

from django.conf.urls import *

urlpatterns = patterns('person_authority.views',
    url(r"$^","app",name="person-authority-default"),
    url(r"search$","search",name="person-authority-search-json")
)
