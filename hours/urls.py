"""
 mod:`url` HoursApplication URL routing
"""
__author__ = 'Jon Driscoll'
import hours.views
from django.conf.urls.defaults import *

urlpatterns = patterns('hours.views',
    url(r"^$","default",name='hours-app-default'),
    url(r"^save$","save",name='hours-app-save'),
    url(r"^manage$","manage",{'message':None},name='hours-app-manage'),
)
