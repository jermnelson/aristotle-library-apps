"""
 mod:`url` Book Search Application URL routing
"""
__author__ = 'Gautam Webb'
import book_search.views
from django.conf.urls.defaults import *

urlpatterns = patterns('book_search.views',
    url(r"^$","default",name='book_search-app-default'),
    url(r'widget$','widget'),
    url(r'dotCMS$','dotCMS'),
    url(r'dotCMSnarrow$','dotCMSnarrow'),
    url(r'dotCMSspeccoll$','dotCMSspeccoll'),

)
                       
