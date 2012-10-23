"""
 mod:`views` Views for MARCR App
"""
__author__ = 'Jeremy Nelson'
import sys,os,logging
from django.views.generic.simple import direct_to_template
from django.http import HttpResponse
import django.utils.simplejson as json
from app_settings import APP
from marcr.forms import *
from marcr.ingesters import ingest_marcfile
from aristotle.settings import INSTITUTION,ANNOTATION_REDIS,AUTHORITY_REDIS
from aristotle.settings import INSTANCE_REDIS,OPERATIONAL_REDIS,WORK_REDIS

def app(request):
    """
    Displays default view for the app

    :param request: HTTP Request
    """
    return direct_to_template(request,
                              'marcr/app.html',
                              {'app':APP,
                               'institution':INSTITUTION,
                               'search_form':MARCRSearchForm(),
                               'user':None})

def manage(request):
    """
    Displays management view for the app

    :param request: HTTP Request
    """
    return direct_to_template(request,
                              'marcr/app.html',
                              {'admin':True,
                               'app':APP,
                               'institution':INSTITUTION,
                               'marc21_form':MARC12toMARCRForm(),
                               'search_form':MARCRSearchForm(),
                               'user':None})


def json_view(func):
    """
    Returns JSON results from method call, from Django snippets
    `http://djangosnippets.org/snippets/622/`_
    """
    def wrap(request, *a, **kw):
        response = None
        try:
            func_val = func(request, *a, **kw)
            assert isinstance(func_val, dict)
            response = dict(func_val)
            if 'result' not in response:
                response['result'] = 'ok'
        except KeyboardInterrupt:
            raise
        except Exception,e:
            exc_info = sys.exc_info()
            print(exc_info)
            logging.error(exc_info)
            if hasattr(e,'message'):
                msg = e.message
            else:
                msg = ugettext("Internal error: %s" % str(e))
            response = {'result': 'error',
                        'text': msg}
            
        json_output = json.dumps(response)
        return HttpResponse(json_output,
                            mimetype='application/json')
    return wrap

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
                                    work_redis=WORK_REDIS)
    return {'total':total_records,'type':'marc21'}
    
                    
    

@json_view
def search(request):
    """
    Searches datastore and returns results as JSON

    :param request: HTTP Request
    """
    output,work_key,instance_keys = {},None,[]
    if request.REQUEST.has_key('work'):
        work_key = request.REQUEST.get('work')
    if request.REQUEST.has_key('instance'):
        instance_keys.append(request.REQUEST.get('instance'))
        if work_key is None:
            work_key = INSTANCE_REDIS.hget(instance_keys[0],'marcr:Work')
        for instance_key in instance_keys:
            if INSTANCE_REDIS.hget(instance_key,'marcr:Work') != work_key:
                return {"result":"error",
                           "msg":"{0} is not assocated as a work with {1}".format(work_key,
                                                                                   instance_key)}
    else:
        instance_keys = WORK_REDIS.smembers("{0}:marcr:Instances".format(work_key)) 
    output["title"] = unicode(WORK_REDIS.hget("{0}:rda:Title".format(work_key),
                                              "rda:preferredTitleForTheWork"),
                              errors="ignore")
    output['ils-bib-numbers'] = []
    for instance_key in instance_keys:
        raw_results['ils-bib-numbers'].append(INSTANCE_REDIS.hget("{0}:rda:identifierForTheManifestation".format(instance_key),
                                                                  'ils-bib-number'))
    output['creators'] = []
    creator_keys = WORK_REDIS.smembers("{0}:rda:creator".format(work_key))
    for creator_key in creator_keys:
        output['creators'].append(unicode(AUTHORITY_REDIS.hget(creator_key,
                                                               "rda:preferredNameForThePerson"),
                                          errors="ignore"))
    return output



    return output


    
    
