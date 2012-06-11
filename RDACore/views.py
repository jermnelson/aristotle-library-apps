"""
 :mod:`views` Views for RDA Core Discovery App
"""
__author__ = "Jeremy Nelson"

from django.views.generic.simple import direct_to_template
from django.http import Http404,HttpResponse,HttpResponseRedirect
from aristotle.settings import INSTITUTION
from app_settings import APP


def default(request):
    """
    Displays default view of the RDA Core Discovery App

    :param request: HTTP Request
    """
    return direct_to_template(request,
                              'rda-core-app.html',
                              {'app':APP,
                               'institution':INSTITUTION})
                               
