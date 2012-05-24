"""
 mod:`views` Call Number Application Views
"""
__author__ = 'Jeremy Nelson'

#import aristotle.lib.rda_core as rda_core,redis
import redis
from django.views.generic.simple import direct_to_template
from django.http import HttpResponse
from django.template import Context,Template,loader
import django.utils.simplejson as json
from django.utils.translation import ugettext
import aristotle.settings as settings
import redis_helpers,sys,logging
import redis_helpers 
from app_settings import APP,SEED_RECORD_ID

redis_server = redis.StrictRedis(host=settings.REDIS_ACCESS_HOST,
                                 port=settings.REDIS_ACCESS_PORT,
                                 db=settings.CALL_NUMBER_DB)


def setup_seed_rec():
    """
    Helper function returns a record based on the SEED_RECORD_ID
    for the default view
    """
    seed_rec = redis_server.hgetall(SEED_RECORD_ID)
    idents = redis_server.hgetall(seed_rec['rdaIdentifierForTheExpression'])
    if idents.has_key('lccn'):
        current = redis_helpers.get_record(idents['lccn'])
    return current

def app(request):
    """
    Returns responsive app view for the Call Number App
    """
    try:
        if request.POST.has_key('call_number'):
            current = redis_helpers.get_record(request.POST['call_number'])
        elif request.GET.has_key('call_number'):
            current = redis_helpers.get_record(request.GET['call_number'])
        if len(current) < 1:
            current = setup_seed_rec()
    except:
        current = setup_seed_rec()
    call_number = get_callnumber(current)
    typeahead_data = redis_helpers.get_all(call_number)
    return direct_to_template(request,
                              'call_number/app.html',
                             {'app':APP,
                              'aristotle_url':settings.DISCOVERY_RECORD_URL,
                              'current':current,
                              'institution':settings.INSTITUTION, 
                              'next':redis_helpers.get_next(call_number),
                              'previous':redis_helpers.get_previous(call_number),
                              'redis':redis_helpers.get_redis_info(),
                              'typeahead_data':typeahead_data})

def default(request):
    """
    Returns the default view for the Call Number Application
    """
    ## return HttpResponse("Call Number Application index")
    current = redis_server.hgetall(SEED_RECORD_ID)
    return direct_to_template(request,
                              'call_number/default.html',
                              {'aristotle_url':settings.DISCOVERY_RECORD_URL,
                               'current':current,
                               'next':redis_helpers.get_next(current['call_number']),
                               'previous':redis_helpers.get_previous(current['call_number']),
                               'redis':redis_helpers.get_redis_info()})


def get_callnumber(rda_record):
    """
    Checks and returns either lccn, sudoc, or local call number. If both lccn and
    local call number exists, the lccn is returned.

    :param rda_record: RDA record info
    :rtype: string of call number
    """
    if rda_record.has_key('sudoc'):
        return rda_record['sudoc']
    elif rda_record.has_key('lccn'):
        return rda_record['lccn']
    elif rda_record.has_key('dewey'):
        return rda_record['dewey']
    elif current.has_key('local'):
        return rda_record['local']
    return None

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
def browse(request):
    """
    JSON view for a call number browser widget view

    :param request: HTTP Request
    """
    call_number = request.GET['call_number']
    current = redis_helpers.get_record(call_number)
    context = Context({'aristotle_url':settings.DISCOVERY_RECORD_URL,
                       'current':current,
                       'next':redis_helpers.get_next(current['call_number']),
                       'previous':redis_helpers.get_previous(current['call_number'])})
    widget_template = loader.get_template('call_number/snippets/widget.html')
    return {'html':widget_template.render(context)}

@json_view
def typeahead_search(request):
    """
    JSON view for typeahead search on call number

    :param request: Request
    """
    query = request.GET['q']
    return redis_helpers.search(query)


def widget(request):
    """
    Returns rendered html snippet of call number browser widget
    """
    standalone = False
    call_number = 'PS21 .D5185 1978'
    if request.method == 'POST':
        if request.POST.has_key('standalone'):
            standalone = request.POST['standalone']
        if request.POST.has_key('call_number'):
            call_number = request.POST['call_number']
    else:
         if request.GET.has_key('standalone'):
            standalone = request.GET['standalone']
         if request.GET.has_key('call_number'):
            call_number = request.GET['call_number']
    current = redis_helpers.get_record(call_number)
    return direct_to_template(request,
                              'call_number/snippets/widget.html',
                              {'aristotle_url':settings.DISCOVERY_RECORD_URL,
                               'current':current,
                               'next':redis_helpers.get_next(call_number),
                               'previous':redis_helpers.get_previous(call_number),

                               'standalone':standalone})
