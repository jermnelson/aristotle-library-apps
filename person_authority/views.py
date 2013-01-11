"""
 mod:`urls` Person Authority App URL routing
"""
__author__ = "Jeremy Nelson"
from app_settings import APP
from django.views.generic.simple import direct_to_template
from aristotle.views import json_view
from aristotle.settings import AUTHORITY_REDIS, INSTANCE_REDIS
from person_authority import person_search
from redis_helpers import process_name
from bibframe.redis_helpers import get_brief

authority_redis = AUTHORITY_REDIS

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


