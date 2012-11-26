"""
 mod:`urls` MARCR  App URL rounting
"""
__author__ = "Jeremy Nelson"

from django.conf.urls.defaults import *
import bibframe.views

urlpatterns = patterns('bibframe.views',
    url(r"$^","app",name="bibframe-default"),
    url(r"ingest$","ingest",name="bibframe-ingest"),
    url(r"manage$","manage",name="bibframe-manage"),
    url(r"search$","search",name="bibframe-json"),
)
