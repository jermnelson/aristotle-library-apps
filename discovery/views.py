"""
 mod:`views` Views for Discovery App
"""

__author__ = "Jeremy Nelson"

import os,random

from django.views.generic.simple import direct_to_template
from django.http import Http404, HttpResponse
from aristotle.views import json_view
from aristotle.forms import FeedbackForm

from app_settings import APP, PAGINATION_SIZE
from bibframe.models import Work,Instance,Person

from discovery.forms import SearchForm
from discovery.redis_helpers import get_facets,get_result_facets,BIBFRAMESearch

from aristotle.settings import INSTITUTION,ANNOTATION_REDIS,AUTHORITY_REDIS
from aristotle.settings import INSTANCE_REDIS,OPERATIONAL_REDIS,CREATIVE_WORK_REDIS


def app(request):
    """
    Displays default view for the app

    :param request: HTTP Request
    """
    results,search_query,message = [],None,None
    if request.method == 'POST':
	query = request.POST.get('q')
	if len(query) > 0:
            bibframe_search = BIBFRAMESearch(q=request.POST.get('q'),
	     		                     authority_ds=AUTHORITY_REDIS,
				             creative_wrk_ds=CREATIVE_WORK_REDIS)
	    bibframe_search.run()
	    search_query = bibframe_search.query
	    for key in bibframe_search.creative_work_keys:
                result = {'work': Work(redis_key=key,
	                               primary_redis=CREATIVE_WORK_REDIS)}
	    
	        results.append(result)
	    facet_list = get_result_facets(bibframe_search.creative_work_keys)
	    message = 'Results for {0}'.format(query)
	else:
            facet_list = get_facets(ANNOTATION_REDIS)
    else:
        facet_list = get_facets(ANNOTATION_REDIS)
#    example = {'work_path': os.path.join("apps",
#	                                 "discovery",
#			                 "work",
#	                                 string(random.randint(0,
#							       int(CREATIVE_WORK_REDIS.get('global bibframe:CreativeWork'))))}
    return direct_to_template(request,
                              'discovery/app.html',
                              {'app': APP,
                               'example':{},
			       'feedback_form':FeedbackForm({'subject':'Discovery App Home'}),
			       'feedback_context':request.get_full_path(),
                               'institution': INSTITUTION,
			       'message':message,
                               'facet_list': facet_list,
			       'results':results,
			       'search_form': SearchForm(),
			       'search_query':search_query,
                               'user': None})

def creative_work(request,redis_id):
    """
    Displays Creative Work View for the discovery app

    :param request: HTTP Request
    :param redis_id: Redis integer for the Creative Work
    """
    redis_key = "bibframe:Work:{0}".format(redis_id)
    if CREATIVE_WORK_REDIS.exists(redis_key):
        creative_work = Work(primary_redis=CREATIVE_WORK_REDIS,
	     	             redis_key=redis_key)
    else:
        raise Http404
    return direct_to_template(request,
		              'discovery/work.html',
			      {'app': APP,
			       'creative_work':creative_work,
			       'feedback_form':FeedbackForm({'subject':'Discovery App Creative Work'}),
			       'feedback_context':request.get_full_path(),
			       'institution': INSTITUTION,
			       'search_form': SearchForm(),
			       'user':None})

def get_pagination(full_path,redis_key,redis_server,offset=0):
    """
    Helper function takes a redis_key and an offset and calculates
    pagination for longer sets

    :param full_path: Full path from the HTTP Request
    :param redis_key: Redis Key
    :param redis_server: Redis instance
    :param offset: Offset, defaults to 0
    """
    total_results = redis_server.llen(redis_key)
    if total_results < 25:
        return None
    total_pages = float(total_results)/PAGINATION_SIZE
    counter,pages = 0,[]
    if total_pages > 6:
        for num in range(0,3):
	    new_offset = num*PAGINATION_SIZE
            page = {'route':'{0}?offset={1}'.format(full_path,
		                                    new_offset),
		    'number':num+1}
	    if offset > num and offset <= new_offset:
	        page['active'] = True
	    pages.append(page)
	pages.append({'route':'',
		      'number':'...',
		      'disabled':True})
	for num in range(int(total_pages-2),int(total_pages)):
	    pages.append({'route':'{0}?offset={1}'.format(full_path,
		                                          offset+(num*PAGINATION_SIZE)),
		          'number':num})
    else:
        for num in range(0,int(total_pages)):
            page = {'route':'{0}?offset={1}'.format(full_path,offset+num),
	            'number':num+1}
	    pages.append(page)
    return {'previous':{'url':'{0}?offset={1}'.format(full_path,offset-PAGINATION_SIZE)},
	    'pages':pages,
	    'next':{'url':'{0}?offset={1}'.format(full_path,offset+PAGINATION_SIZE)}}

			    

def facet_detail(request,facet_name,facet_item):
    """
    Displays a specific Facet listing
    """
    redis_key = "bibframe:Annotation:Facet:{0}:{1}".format(facet_name,facet_item)
    listing_key = "facet-listing:{0}:{1}".format(facet_name,facet_item)
    if not ANNOTATION_REDIS.exists(redis_key):
        raise Http404
    if not ANNOTATION_REDIS.exists(listing_key):
        ANNOTATION_REDIS.sort(redis_key,alpha=True,store=listing_key)
        ANNOTATION_REDIS.expire(listing_key,86400)
    offset =  int(request.REQUEST.get('offset',0))
    records = []
    pagination = get_pagination(request.path,
		                listing_key,
				ANNOTATION_REDIS,
				offset)
    record_slice = ANNOTATION_REDIS.lrange(listing_key,
		                           offset,
					   offset+PAGINATION_SIZE)
    for row in record_slice:
        if row.find("Instance") > -1:
            work_key = INSTANCE_REDIS.hget(row,'instanceOf')
        elif row.find("Work") > -1:
            work_key = row
        work = Work(primary_redis=CREATIVE_WORK_REDIS,
                    redis_key=work_key)
        records.append({'work':work})
    return direct_to_template(request,
                              'discovery/app.html',
                              {'app': APP,
                               'example':{},
			       'feedback_form':FeedbackForm({'subject':'Discovery Facet Display'}),
			       'feedback_context':request.get_full_path(),
                               'institution': INSTITUTION,
                               'facet_list': None,
			       'message':"Results for Facet {0}:{1}".format(facet_name,facet_item),
			       'pagination':pagination,
			       'results':records,
			       'search_form': SearchForm(),
			       'search_query': None,
                               'user': None})

                              

    return HttpResponse("In facet detail key={0}\n{1}".format(redis_key,records))

def facet_summary(request,facet_name):
    """
    Displays A general facet with all of its's items
    """
    redis_key = "bibframe:Annnotation:Facet:{0}s".format(facet_name)
    if not ANNOTATION_REDIS.exists(redis_key):
        raise Http404
    return HttpResponse("In facet_summary, Facet = {0}".format(redis_key))
    

def instance(request,redis_id):
    """
    Instance view for the discovery app

    :param request: HTTP Request
    :param redis_id": Redis integer for the Instance
    """
    redis_key = "bibframe:Instance:{0}".format(redis_id)
    if INSTANCE_REDIS.exists(redis_key):
        instance = Instance(primary_redis=INSTANCE_REDIS,
			    redis_key=redis_key)
    else:
        raise Http404
    return direct_to_template(request,
		              'discovery/instance.html',
			      {'app': APP,
			       'feedback_form':FeedbackForm({'subject':'Discovery App Instance'}),
			       'feedback_context':request.get_full_path(),
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
    redis_key = "bibframe:Person:{0}".format(redis_id)
    if AUTHORITY_REDIS.exists(redis_key):
        person = Person(primary_redis=AUTHORITY_REDIS,
			redis_key=redis_key)
    else:
        raise Http404
    return direct_to_template(request,
		              'discovery/person.html',
			      {'app': APP,
			       'feedback_form':FeedbackForm({'subject':'Discovery App Person'}),
			       'feedback_context':request.get_full_path(),
			       'institution': INSTITUTION,
			       'person':person,
			       'search_form': SearchForm(),
			       'user':None})

