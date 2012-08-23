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
from app_settings import APP,SEED_RECORD_ID,REDIS_SERVER

redis_server = REDIS_SERVER

def setup_seed_rec():
    """
    Helper function returns a record based on the SEED_RECORD_ID
    for the default view
    """
    seed_rec = redis_server.hgetall(SEED_RECORD_ID)
    ident_key = '{0}:identifiers'.format(SEED_RECORD_ID)
    idents = redis_server.hgetall(ident_key)
    if idents.has_key('lccn'):
        current = redis_helpers.get_record(call_number=idents['lccn'])
    return current

def app(request):
    """
    Returns responsive app view for the Call Number App
    """

    try:
        current = redis_helpers.get_record(call_number=request.REQUEST.get('call_number'))
    except:
        print("{0}".format(sys.exc_info()))
        current = setup_seed_rec()
    call_number = current.get('call_number')
    next_recs = redis_helpers.get_next(call_number,
                                      call_number_type=current['type_of'])
    previous_recs = redis_helpers.get_previous(call_number,
                                               call_number_type=current['type_of'])
    return direct_to_template(request,
                              'call_number/app.html',
                             {'app':APP,
                              'aristotle_url':settings.DISCOVERY_RECORD_URL,
                              'current':current,
                              'institution':settings.INSTITUTION, 
                              'next':next_recs,
                              'previous':previous_recs,
                              'redis':redis_helpers.redis_server.info(),
                              'typeahead_data':None})

def default(request):
    """
    Returns the default view for the Call Number Application
    """
    ## return HttpResponse("Call Number Application index")
    seed_key = '{0}:identifiers'.format(SEED_RECORD_ID)
    current = redis_server.hgetall()
    return direct_to_template(request,
                              'call_number/default.html',
                              {'aristotle_url':settings.DISCOVERY_RECORD_URL,
                               'current':current,
                               'next':redis_helpers.get_next(current['lccn']),
                               'previous':redis_helpers.get_previous(current['lccn']),
                               'redis':redis_helpers.redis_server.info()})


def get_callnumber(rda_record):
    """
    Checks and returns either lccn, sudoc, or local call number. If both lccn and
    local call number exists, the lccn is returned.

    :param rda_record: RDA record info
    :rtype: string of call number
    """
    ident_key = rda_record.get("identifiers")
    if redis_server.hexists(ident_key,'sudoc'):
        return redis_server.hget(ident_key,'sudoc')
    elif redis_server.hexists(ident_key,'lccn'):
        return redis_server.hget(ident_key,'lccn')
    elif redis_server.hexists(ident_key,'dewey'):
        return redis_server.hget(ident_key,'dewey')
    elif redis_server.hexists(ident_key,'local'):
        return redis_server.hget(ident_key,'local')
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
    current = redis_helpers.get_record(call_number=call_number)
    next_recs = redis_helpers.get_next(call_number)
    previous_recs = redis_helpers.get_previous(call_number)
    context = Context({'aristotle_url':settings.DISCOVERY_RECORD_URL,
                       'current':current,
                       'next':next_recs,
                       'previous':previous_recs})
    widget_template = loader.get_template('call_number/snippets/widget.html')
    return {'html':widget_template.render(context)}

@json_view
def term_search(request):
    """
     JSON view that outputs a list of record's legacy bib numbers in JSON

    :param request: Djagno HTTP Request
    """
    call_number=request.REQUEST.get('call_number')
    if request.REQUEST.has_key("type"):
        call_number_type = request.REQUEST.get('type')
    else:
        call_number_type = "lccn"
    if request.REQUEST.has_key("slice-size"):
        slice_size = int(request.REQUEST.get('slice-size'))
    else:
        slice_size = 2 # Default assumes browse display of two results
    current = redis_helpers.get_record(call_number=call_number)
    bib_numbers = []
    if current is not None:
        bib_numbers.append(current.get('bib_number'))
        current_rank = redis_helpers.get_rank(call_number,
                                              call_number_type=call_number_type)
        
        next_recs = redis_helpers.get_slice(current_rank+1,
                                            current_rank+slice_size,
                                            call_number_type)
        for row in next_recs:
            bib_numbers.append(row.get('bib_number'))
        previous_recs = redis_helpers.get_previous(call_number,
                                                   call_number_type=call_number_type)
        for row in previous_recs:
            bib_numbers.insert(0,row.get('bib_number'))
    return {'bib_numbers':bib_numbers}


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
    current = redis_helpers.get_record(call_number=call_number)
    return direct_to_template(request,
                              'call_number/snippets/widget.html',
                              {'aristotle_url':settings.DISCOVERY_RECORD_URL,
                               'current':current,
                               'next':redis_helpers.get_next(call_number),
                               'previous':redis_helpers.get_previous(call_number),
                               'standalone':standalone})
