"""
 mod:`views` Views for Discovery App
"""

__author__ = "Jeremy Nelson"

from django.views.generic.simple import direct_to_template
from aristotle.views import json_view

from app_settings import APP
from discovery.forms import SearchForm
from discovery.redis_helpers import get_facets

from aristotle.settings import INSTITUTION,ANNOTATION_REDIS,AUTHORITY_REDIS
from aristotle.settings import INSTANCE_REDIS,OPERATIONAL_REDIS,CREATIVE_WORK_REDIS


def app(request):
    """
    Displays default view for the app

    :param request: HTTP Request
    """
    facet_list = get_facets(ANNOTATION_REDIS)
    return direct_to_template(request,
                              'discovery/app.html',
                              {'app': APP,
                               'institution': INSTITUTION,
                               'facet_list': facet_list,
                               'search_form': SearchForm(),
                               'user': None})
