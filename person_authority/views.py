"""
 mod:`urls` Person Authority App URL routing
"""
__author__ = "Jeremy Nelson"
from app_settings import APP
from django.shortcuts import render as direct_to_template # quick hack to get running under django 1.5
from django.shortcuts import render
from aristotle.views import json_view
from aristotle.settings import REDIS_DATASTORE
from redis_helpers import person_search, process_name
from bibframe.redis_helpers import get_brief


def app(request):
    """
    Default view for Person Authority App
    """
    return direct_to_template(request,
                              'person_authority/app.html',
                              {'app':APP})


@json_view
def search(request):
    """
    JSON search view returns the results of searching the Authority Redis
    datastore.

    :param request: HTTP Request
    """
    raw_name = request.REQUEST.get("q")
    output = person_search(raw_name)
    return {'results':output}


