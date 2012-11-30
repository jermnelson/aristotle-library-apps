"""
 mod:`views` Views for MARCR App
"""
__author__ = 'Jeremy Nelson'
import sys,os,logging,datetime,re
from django.views.generic.simple import direct_to_template
from django.http import HttpResponse
import django.utils.simplejson as json
from app_settings import APP
from aristotle.views import json_view
from bibframe.forms import *
from bibframe.ingesters import ingest_marcfile
from aristotle.settings import INSTITUTION,ANNOTATION_REDIS,AUTHORITY_REDIS
from aristotle.settings import INSTANCE_REDIS,OPERATIONAL_REDIS,CREATIVE_WORK_REDIS

def annotation(request,redis_key):
    """
    Displays a generic view of a BIBFRAME Annotation

    :param request: HTTP Request
    :param redis_key: Redis key of the Annotation
    """
    add_use(redis_key,ANNOTATION_REDIS)
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
                               'institution':INSTITUTION,
                               'search_form':MARCRSearchForm(),
                               'user':None})

def authority(request,redis_key):
    """
    Displays a generic view of a BIBFRAME Authority

    :param request: HTTP Request
    :param redis_key: Redis key of the Authority
    """
    add_use(redis_key,AUTHORITY_REDIS)
    return direct_to_template(request,
                              'bibframe/authority.html',
                              {'app':APP,
                               'institution':INSTITUTION,
                               'user':None})



def creative_work(request,redis_key):
    """
    Displays a generic view of a BIBFRAME Authority

    :param request: HTTP Request
    :param redis_key: Redis key of the Authority
    """
    # Tracks usage of the creative work by the hour
    add_use(redis_key,CREATIVE_WORK_REDIS)
    return direct_to_template(request,
                              'bibframe/creative_work.html',
                              {'app':APP,
                               'institution':INSTITUTION,
                               'user':None})

def instance(request,redis_key):
    """
    Displays a generic view of a BIBFRAME Instance

    :param request: HTTP Request
    :param redis_key: Redis key of the Authority
    """
    add_use(redis_key,INSTANCE_REDIS)
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
    return {'total':total_records,'type':'marc21'}
    
                    
    

@json_view
def search(request):
    """
    Searches datastore and returns results as JSON

    :param request: HTTP Request
    """
    output,work_key,instance_keys = {},None,[]
    if request.REQUEST.has_key('creative_work'):
        creative_work_key = request.REQUEST.get('creative_work')
    if request.REQUEST.has_key('instance'):
        instance_keys.append(request.REQUEST.get('instance'))
        if work_key is None:
            work_key = INSTANCE_REDIS.hget(instance_keys[0],'bibframe:Work')
        for instance_key in instance_keys:
            if INSTANCE_REDIS.hget(instance_key,'bibframe:Work') != work_key:
                return {"result":"error",
                           "msg":"{0} is not assocated as a work with {1}".format(creative_work_key,
                                                                                  instance_key)}
    else:
        instance_keys = CREATIVE_WORK_REDIS.smembers("{0}:bibframe:Instances".format(creative_work_key)) 
    output["title"] = unicode(CREATIVE_WORK_REDIS.hget("{0}:rda:Title".format(creative_work_key),
                                                      "rda:preferredTitleForTheWork"),
                              errors="ignore")
    output['ils-bib-numbers'] = []
    for instance_key in instance_keys:
        raw_results['ils-bib-numbers'].append(INSTANCE_REDIS.hget("{0}:rda:identifierForTheManifestation".format(instance_key),
                                                                  'ils-bib-number'))
    output['creators'] = []
    creator_keys = CREATIVE_WORK_REDIS.smembers("{0}:rda:creator".format(work_key))
    for creator_key in creator_keys:
        output['creators'].append(unicode(AUTHORITY_REDIS.hget(creator_key,
                                                               "rda:preferredNameForThePerson"),
                                          errors="ignore"))
    return output
    
# Helper functions
usage_key_re = re.compile(r"(\w+)\:(\d+)")
def add_use(redis_key,redis_ds):
    """
    Helper function records the usage of a BIBFRAME entity. Usage is tracked
    by the hour; this could be adjusted in the future for finer-grained usage
    by the minute or even by the second

    :param redis_key: Redis key
    :param redis_ds: Redis datastore
    """
    now = datetime.datetime.utcnow()
    usage_key_search = usage_key_re.search(redis_key)
    if usage_key_search is not None:
        entity_name,key_num = usage_key_search.groups()
        usage_key = "bibframe:{0}:usage:{1}".format(entity_name,
                                                    now.strftime("%Y-%m-%dT%H"))
        redis_ds.setbit(usage_key,int(key_num),1)
