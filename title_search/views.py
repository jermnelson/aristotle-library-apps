"""
 mod:`views` Title Search App Views
"""
__author__ = "Jeremy Nelson"

from app_settings import APP,REDIS_SERVER
from django.views.generic.simple import direct_to_template
from django.http import HttpResponse
from django.template import Context,Template,loader
import aristotle.settings as settings
import json,sys,logging
import search_helpers

authority_redis = settings.AUTHORITY_REDIS
instance_redis = settings.INSTANCE_REDIS
work_redis = settings.WORK_REDIS

def app(request):
    """
    Returns app view for Title Search App

    :param request: HTTP Request
    """
    return direct_to_template(request,
                              'title_search/app.html',
                              {'app':APP,
                               'aristotle_url':settings.DISCOVERY_RECORD_URL})


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
def search(request):
    """
    JSON Ajax view, accepts a query and returns the results
    from searching RDA Title Redis datastore instance.

    :param request: HTTP Request
    :param rtype: JSON encoded string
    """
    results = []
    raw_title = request.REQUEST.get('q')
    if raw_title is not None:
        search_results = search_helpers.search_title(raw_title,work_redis)
        if len(search_results) > 0:
            for work_key in search_results:
                raw_results = work_redis.hgetall(work_key)
                for k,v in raw_results.iteritems():
                    raw_results[k] = v.encode('utf8','replace')
                raw_results["marcr_work"] = work_key
                raw_results['search_prefix'] = raw_title
                raw_results['title'] = unicode(work_redis.hget("{0}:rda:Title".format(work_key),
                                                               'rda:preferredTitleForTheWork'),
                                               errors="replace")
                raw_results['ils-bib-numbers'] = []
                for instance_key in list(work_redis.smembers("{0}:marcr:Instances".format(work_key))):
                     raw_results['ils-bib-numbers'].append(instance_redis.hget("{0}:rda:identifierForTheManifestation".format(instance_key),
                                                                               'ils-bib-number'))
                creator_keys = work_redis.smembers("{0}:rda:creator".format(work_key))
                if len(creator_keys) > 0:
                    raw_results['creator'] = []
                    creator_keys = list(creator_keys)
                    for creator_key in creator_keys:
                        creator_name = unicode(authority_redis.hget(creator_key,
                                                                    "rda:preferredNameForThePerson"),
                                               errors="replace")
                        raw_results['creator'].append(creator_name)
                results.append(raw_results)
    return {'q':raw_title,'results':results}
    
            
        
    
    
