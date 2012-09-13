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

redis_server = REDIS_SERVER

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
        search_results = search_helpers.search_title(raw_title,redis_server)
        if len(search_results) > 0:
            for title_key in search_results:
                raw_results = redis_server.hgetall(title_key)
                for k,v in raw_results.iteritems():
                    raw_results[k] = v.decode('utf8','ignore')
                results.append(raw_results)
    return {'q':raw_title,'results':results}
    
            
        
    
    
