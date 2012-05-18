"""
 mod:`views` Default Views for Aristotle App
"""
__author__ = 'Jeremy Nelson'

from django.views.generic.simple import direct_to_template
import django.utils.simplejson as json
from settings import INSTITUTION
from fixures import json_loader,rst_loader

def default(request):
    """
    Default view for the portfolio app displays both Access and Productivity
    Apps depending on authentication and access rights

    :param request: Web request from client
    :rtype: Generated HTML template
    """
    app_listing = []
    
    return direct_to_template(request,
                              'index.html',
                              {'app':None,
                               'institution':INSTITUTION,
                               'navbar_menus':json_loader.get('navbar-menus'),
                               'portfolio':app_listing,
                               'vision':rst_loader.get('vision-for-aristotle-library-apps'),
                               'user':None})
