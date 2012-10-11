"""
 mod:`urls` MARCR  App URL rounting
"""
__author__ = "Jeremy Nelson"

from django.conf.urls.defaults import *
import marcr.views

urlpatterns = patterns('marcr.views',
    url(r"$^","app",name="marcr-default"),
    url(r"ingest$","ingest",name="marcr-ingest"),
    url(r"manage$","manage",name="marcr-manage"),
    url(r"search$","search",name="marcr-json"),
)
