"""
 mod:`views` Call Number Application Views
"""
__author__ = 'Jeremy Nelson'

#import aristotle.lib.rda_core as rda_core,redis
import redis
from django.shortcuts import render as direct_to_template # quick hack to get running under django 1.5
from django.shortcuts import render

from django.http import HttpResponse
from django.template import Context,Template,loader
import django.utils.simplejson as json
from django.utils.translation import ugettext
import aristotle.settings as settings
from aristotle.settings import REDIS_DATASTORE
from aristotle.views import json_view
from aristotle.forms import FeedbackForm
import redis_helpers,sys,logging
from app_settings import APP,SEED_RECORD_ID




def setup_seed_rec():
    """
    Helper function returns a record based on the SEED_RECORD_ID
    for the default view
    """
    if REDIS_DATASTORE.hexists(SEED_RECORD_ID,'callno-lcc'):
        lcc = REDIS_DATASTORE.hget(SEED_RECORD_ID,'callno-lcc')
        current = redis_helpers.get_record(call_number=lcc)
        return current
    else:
        return None

def app(request):
    """
    Returns responsive app view for the Call Number App
    """
    call_number=request.REQUEST.get('call_number',None)
    if call_number is not None:
        current = redis_helpers.get_record(call_number=call_number)
    else:
        current = setup_seed_rec()
    call_number = current.get('call_number')
    next_recs = redis_helpers.get_next(call_number,
                                       call_number_type=current['type_of'])
    print(next_recs)
    previous_recs = redis_helpers.get_previous(call_number,
                                               call_number_type=current['type_of'])
    return direct_to_template(request,
                              'call_number/app.html',
                             {'app':APP,
                              'aristotle_url':settings.DISCOVERY_RECORD_URL,
                              'current':current,
			      'feedback_context':request.get_full_path(),
			      'feedback_form':FeedbackForm({'subject':'Call Number App'}),
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
    current = redis_server.hgetall(seed_key)
    return direct_to_template(request,
                              'call_number/default.html',
                              {'aristotle_url': settings.DISCOVERY_RECORD_URL,
                               'current': current,
                               'next': redis_helpers.get_next(current['lccn']),
                               'previous': redis_helpers.get_previous(
                                   current['lccn']),
                               'redis': redis_helpers.redis_server.info()})


def get_callnumber(rda_record):
    """
    Checks and returns either lccn, sudoc, or local call number. If both lccn
    and local call number exists, the lccn is returned.

    :param rda_record: RDA record info
    :rtype: string of call number
    """
    ident_key = rda_record.get("identifiers")
    if redis_server.hexists(ident_key, 'sudoc'):
        return redis_server.hget(ident_key, 'sudoc')
    elif redis_server.hexists(ident_key, 'lccn'):
        return redis_server.hget(ident_key, 'lccn')
    elif redis_server.hexists(ident_key, 'dewey'):
        return redis_server.hget(ident_key, 'dewey')
    elif redis_server.hexists(ident_key, 'local'):
        return redis_server.hget(ident_key, 'local')
    return None


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
def discovery_search(request):
    """
    Supports discovery layer search

    :param request: HTTP Request
    """
    brief_marcr = []
    call_number = request.REQUEST.get('q')
    if request.REQUEST.has_key("type"):
        call_number_type = request.REQUEST.get('type')
    else:
        call_number_type = "lcc"
    if request.REQUEST.has_key("slice-size"):
        slice_size = int(request.REQUEST.get('slice-size'))
    else:
        slice_size = 20
    rank = redis_helpers.get_rank(call_number,
                                  call_number_type=call_number_type)
    call_num_slice  = redis_server.zrange("{0}-sort-set".format(call_number_type),
                                          rank,
                                          rank+slice_size)
    instance_keys = []
    for call_num in call_num_slice:
        instance_keys.append(redis_server.hget('{0}-hash'.format(call_number_type),
                                               call_num))
    for key in instance_keys:
        rec = marcr.app_helpers.get_brief(redis_authority=settings.AUTHORITY_REDIS,
                                          redis_instance=settings.INSTANCE_REDIS,
                                          redis_work=settings.WORK_REDIS,
                                          instance_key=key)
        rec["search_prefix"] = redis_server.hget("{0}:rda:identifierForTheManifestation".format(key),
                                                 call_number_type)
        brief_marcr.append(rec)
    return {'results':brief_marcr}

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
def widget_search(request):
    """
    JSON view for widget search on call number

    :param request: Request
    """
    call_number = request.REQUEST.get('q')
    if "type" in request.REQUEST:
        call_number_type = request.REQUEST.get('type')
    else:
        call_number_type = "lcc"
    current = redis_helpers.get_record(call_number=call_number,
                                       call_number_type=call_number_type)
    next_recs = redis_helpers.get_next(call_number, call_number_type)
    previous_recs = redis_helpers.get_previous(call_number, call_number_type)
    return {
        'current': current,
        'nextRecs': next_recs,
        'previousRecs': previous_recs
        }



def widget(request):
    """
    Returns rendered html snippet of call number browser widget
    """
    standalone = False
    call_number = 'PS21 .D5185 1978'
    if 'standalone' in request.REQUEST:
        standalone = request.REQUEST.get('standalone')
    if 'call_number' in request.REQUEST:
        call_number = request.REQUEST.get('call_number')
    current = redis_helpers.get_record(call_number=call_number)
    return direct_to_template(request,
                              'call_number/snippets/widget.html',
                              {'aristotle_url': settings.DISCOVERY_RECORD_URL,
                               'current': current,
                               'next': redis_helpers.get_next(call_number),
                               'previous': redis_helpers.get_previous(
                                   call_number),
                               'standalone': standalone})
