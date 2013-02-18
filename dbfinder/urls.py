__author__ = "Diane Westerfield"
__author__ = "Jeremy Nelson"

import dbfinder.views
from django.conf.urls import patterns, include, url

urlpatterns = patterns('dbfinder.views',
    url(r"^$","app",name="dbfinder-default"),
    url(r"^(\w+).json$","alpha_json",name="dbfinder-alpha-json"),
    url(r"^(\w+)$","alpha",name="dbfinder-alpha"),
    url(r"^subjects/([\w ]+).json$","subject_json",name="dbfinder-subject-json"),
    url(r"^subjects/([\w ]+)$","subject",name="dbfinder-subject"),
   
)
