__author__ = "Diane Westerfield"
__author__ = "Jeremy Nelson"

import dbfinder.views
from django.conf.urls import patterns, include, url

urlpatterns = patterns('dbfinder.views',
    url(r"^$","app",name="dbfinder-default"),
)
