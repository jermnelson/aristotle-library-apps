"""
 mod:`views` Views for Discovery App
"""

__author__ = "Jeremy Nelson"

from django.views.generic.simple import direct_to_template
from django.http import Http404
from aristotle.views import json_view

from app_settings import APP
from bibframe.bibframe_models import CreativeWork,Instance,Person

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

def creative_work(request,redis_id):
    """
    Displays Creative Work View for the discovery app

    :param request: HTTP Request
    :param redis_id: Redis integer for the Creative Work
    """
    redis_key = "bibframe:CreativeWork:{0}".format(redis_id)
    if CREATIVE_WORK_REDIS.exists(redis_key):
        creative_work = CreativeWork(redis=CREATIVE_WORK_REDIS,
	     	                     redis_key=redis_key)
    else:
        raise Http404
    return direct_to_template(request,
		              'discovery/work.html',
			      {'app': APP,
			       'creative_work':creative_work,
			       'institution': INSTITUTION,
			       'search_form': SearchForm(),
			       'user':None})

def instance(request,redis_id):
    """
    Instance view for the discovery app

    :param request: HTTP Request
    :param redis_id": Redis integer for the Instance
    """
    redis_key = "bibframe:Instance:{0}".format(redis_id)
    if INSTANCE_REDIS.exists(redis_key):
        instance = Instance(redis=INSTANCE_REDIS,
			    redis_key=redis_key)
    else:
        raise Http404
    return direct_to_template(request,
		              'discovery/instance.html',
			      {'app': APP,
			       'instance':instance,
			       'institution': INSTITUTION,
			       'search_form': SearchForm(),
			       'user':None})


def person(request,redis_id):
    """
    Person view for the discovery app

    :param request: HTTP Request
    :param redis_id": Redis integer for the Person
    """
    redis_key = "bibframe:Authority:Person:{0}".format(redis_id)
    if AUTHORITY_REDIS.exists(redis_key):
        person = Person(redis=AUTHORITY_REDIS,
			redis_key=redis_key)
    else:
        raise Http404
    return direct_to_template(request,
		              'discovery/person.html',
			      {'app': APP,
			       'institution': INSTITUTION,
			       'person':person,
			       'search_form': SearchForm(),
			       'user':None})

