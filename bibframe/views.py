"""
 mod:`views` Views for BIBFRAME App
"""
__author__ = 'Jeremy Nelson'
import datetime
import re

from django.views.generic.simple import direct_to_template

from bibframe.app_settings import APP
from aristotle.views import json_view
from bibframe.forms import MARCRSearchForm, MARC12toMARCRForm
from bibframe.ingesters.MARC21 import ingest_marcfile
from aristotle.forms import FeedbackForm
from aristotle.settings import INSTITUTION, ANNOTATION_REDIS, AUTHORITY_REDIS
from aristotle.settings import INSTANCE_REDIS
from aristotle.settings import CREATIVE_WORK_REDIS

def annotation(request,
               redis_key):
    """
    Displays a generic view of a BIBFRAME Annotation

    :param request: HTTP Request
    :param redis_key: Redis key of the Annotation
    """
    add_use(redis_key, ANNOTATION_REDIS)
    return direct_to_template(request,
                              'bibframe/annotation.html',
                              {'app':APP,
                               'institution':INSTITUTION,
                               'user':None})


def app(request):
    """
    Displays default view for the app

    :param request: HTTP Request
    """
    return direct_to_template(request,
                              'bibframe/app.html',
                              {'app':APP,
			       'feedback_form':FeedbackForm({'subject':'BIBFRAME App'}),
			       'feedback_context':request.get_full_path(),
                               'institution':INSTITUTION,
                               'search_form':MARCRSearchForm(),
                               'user':None})

def authority(request,
              redis_key):
    """
    Displays a generic view of a BIBFRAME Authority

    :param request: HTTP Request
    :param redis_key: Redis key of the Authority
    """
    add_use(redis_key, AUTHORITY_REDIS)
    return direct_to_template(request,
                              'bibframe/authority.html',
                              {'app':APP,
                               'institution':INSTITUTION,
                               'user':None})



def creative_work(request,
                  redis_key):
    """
    Displays a generic view of a BIBFRAME Creative Work

    :param request: HTTP Request
    :param redis_key: Redis key of the Creative Work 
    """
    # Tracks usage of the creative work by the hour
    add_use(redis_key, CREATIVE_WORK_REDIS)
    return direct_to_template(request,
                              'bibframe/creative_work.html',
                              {'app':APP,
                               'institution':INSTITUTION,
                               'user':None})

def instance(request,
             redis_key):
    """
    Displays a generic view of a BIBFRAME Instance

    :param request: HTTP Request
    :param redis_key: Redis key of the Authority
    """
    add_use(redis_key, INSTANCE_REDIS)
    return direct_to_template(request,
                              'bibframe/instance.html',
                              {'app':APP,
                               'institution':INSTITUTION,
                               'user':None})


def manage(request):
    """
    Displays management view for the app

    :param request: HTTP Request
    """
    return direct_to_template(request,
                              'bibframe/app.html',
                              {'admin':True,
                               'app':APP,
                               'institution':INSTITUTION,
                               'marc21_form':MARC12toMARCRForm(),
                               'search_form':MARCRSearchForm(),
                               'user':None})

# JSON Views
@json_view
def ingest(request):
    "JSON view for ingesting records into RLSP"
    if request.REQUEST.get('type') == 'marc21':
        return ingest_marc21(request)
    elif request.REQUEST.get('type') == 'mods':
        return {'error':'Not implemented'}
    else:
        return {'error':'Ingester type not found'}

def ingest_marc21(request):
    """
    Ingests MARC21 file into datastore
    """
    marc_filename = request.REQUEST.get('file_location')
    total_records = ingest_marcfile(marc_filename=marc_filename,
                                    annotation_redis=ANNOTATION_REDIS,
                                    authority_redis=AUTHORITY_REDIS,
                                    instance_redis=INSTANCE_REDIS,
                                    work_redis=CREATIVE_WORK_REDIS)
    return {'total':total_records,
            'type':'marc21'}


# Helper functions
USAGE_KEY_RE = re.compile(r"(\w+)\:(\d+)")
def add_use(redis_key,
            redis_ds):
    """
    Helper function records the usage of a BIBFRAME entity. Usage is tracked
    by the hour; this could be adjusted in the future for finer-grained usage
    by the minute or even by the second

    Parameters:
    redis_key -- Redis key
    redis_ds -- Redis datastore
    """
    now = datetime.datetime.utcnow()
    usage_key_search = USAGE_KEY_RE.search(redis_key)
    if usage_key_search is not None:
        entity_name, key_num = usage_key_search.groups()
        usage_key = "bf:{0}:usage:{1}".format(entity_name,
                                              now.strftime("%Y-%m-%dT%H"))
        redis_ds.setbit(usage_key,
                        int(key_num),
                        1)
