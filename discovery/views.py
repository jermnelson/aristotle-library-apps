"""
 mod:`views` Views for Discovery App
"""

__author__ = "Jeremy Nelson"

import os
import random

from django.views.generic.simple import direct_to_template
from django.shortcuts import render
from django.http import Http404, HttpResponse
from aristotle.views import json_view
from aristotle.forms import FeedbackForm

from app_settings import APP, PAGINATION_SIZE
from bibframe.models import Work,Instance,Person
from bibframe.models import CREATIVE_WORK_CLASSES

import bibframe.models
from bibframe.redis_helpers import get_json_linked_data

from discovery.forms import SearchForm
from discovery.redis_helpers import get_facets, get_result_facets, BIBFRAMESearch
from discovery.redis_helpers import get_news


from aristotle.settings import INSTITUTION
from aristotle.settings import REDIS_DATASTORE
from aristotle.settings import FEATURED_INSTANCES



def app(request):
    """
    Displays default view for the app

    :param request: HTTP Request
    """
    results,search_query,message = [],None,None
    if request.method == 'POST':
        query = request.POST.get('q')
        type_of = request.POST.get('q_type')
        if len(query) > 0:
            bibframe_search = BIBFRAMESearch(q=query,
                                             type_of=type_of,
                                             redis_datastore=REDIS_DATASTORE)
            bibframe_search.run()
            search_query = bibframe_search.query

            message = 'Results for {0}'.format(query)
            results = bibframe_search.creative_works()
            facet_list = bibframe_search.facets
            if len(results) < 1:
                message = 'No Results found for {0}'.format(query)
        else:
            message = 'No search terms provided'
            facet_list = get_facets(REDIS_DATASTORE)
    else:
        facet_list = get_facets(REDIS_DATASTORE)
#    example = {'work_path': os.path.join("apps",
#                                    "discovery",
#                            "work",
#                                    string(random.randint(0,
#   int(REDIS_DATASTORE.get('global bibframe:CreativeWork'))))}
    featured_instances = []
    for instance_key in FEATURED_INSTANCES:
        cover_art_key = None
        instance_link = '/apps/discovery/Instance/{0}'.format(
            instance_key.split(":")[-1])
        for annotation_key in REDIS_DATASTORE.smembers(
            '{0}:hasAnnotation'.format(instance_key)):
            if annotation_key.startswith('bf:CoverArt'):
                cover_art_key = annotation_key
        work_key = REDIS_DATASTORE.hget(instance_key,
                                       'instanceOf')
        cover_id = cover_art_key.split(":")[-1]
        cover_url = '/apps/discovery/CoverArt/{0}-'.format(cover_id)
        if REDIS_DATASTORE.hexists(cover_art_key, 'annotationBody'):
            cover_url += "body.jpg"
        else:
            cover_url += 'thumbnail.jpg'
        featured_instances.append(
            {'cover': cover_url,
             'title': REDIS_DATASTORE.hget(
                '{0}:title'.format(work_key),
                'rda:preferredTitleForTheWork'),
             'instance': instance_link})
    
    return direct_to_template(request,
                              'discovery/app.html',
                              {'app': APP,
                               'example': {},
                               'featured': featured_instances, 
                   'feedback_form':FeedbackForm({'subject':'Discovery App Home'}),
                   'feedback_context':request.get_full_path(),
                               'institution': INSTITUTION,
                   'message':message,
                               'facet_list': facet_list,
                               'news_feed': get_news(),
                   'results':results,
                   'search_form': SearchForm(),
                   'search_query':search_query,
                               'user': None})


def creative_work(request, redis_id):
    """
    Displays Creative Work View for the discovery app

    :param request: HTTP Request
    :param redis_id: Redis integer for the Creative Work
    """
    redis_key = "bf:Work:{0}".format(redis_id)
    if REDIS_DATASTORE.exists(redis_key):
        creative_work = Work(redis_datastore=REDIS_DATASTORE,
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



def display_cover_image(request, redis_id, type_of, image_ext):
    """
    Returns a cover image based on the CoverArt's redis key,
    if the type-of is body or thumbnail and the image_ext is
    either "jpg", "png", or "gif"
    
    :param redis_id: Redis key id of the bibframe:CoverArt 
    :param type_of: Should be either "thumbnail" or "body" 
    "param image_ext: The images extension
    """
    redis_key = "bf:CoverArt:{0}".format(redis_id)
    if type_of == 'thumbnail':
        raw_image = REDIS_DATASTORE.hget(redis_key, 
                                          'thumbnail')
    elif type_of == 'body':
        raw_image = REDIS_DATASTORE.hget(redis_key, 
                                          'annotationBody')
    if raw_image is None:
        raise Http404
    return HttpResponse(raw_image, 
                        mimetype="image/{0}".format(image_ext))


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

                

def facet_detail(request, facet_name, facet_item):
    """Displays a specific Facet listing

    Parameters:
    facet_name -- Name of the Facet
    facet_item -- Name of the Facet item
    """
    redis_key = "bf:Annotation:Facet:{0}:{1}".format(facet_name,facet_item)
    listing_key = "facet-listing:{0}:{1}".format(facet_name,facet_item)
    if not REDIS_DATASTORE.exists(redis_key):
        raise Http404
    if not REDIS_DATASTORE.exists(listing_key):
        REDIS_DATASTORE.sort(redis_key,
                             alpha=True,
                             store=listing_key)
        REDIS_DATASTORE.expire(listing_key,86400)
    offset =  int(request.REQUEST.get('offset',0))
    records = []
    pagination = get_pagination(request.path,
                        listing_key,
                REDIS_DATASTORE,
                offset)
    record_slice = REDIS_DATASTORE.lrange(listing_key,
                                   offset,
                       offset+PAGINATION_SIZE)
    for row in record_slice:
        if row.find("Instance") > -1:
            work_key = REDIS_DATASTORE.hget(row, 'instanceOf')
        elif row.find("Work") > -1:
            work_key = row
        work = Work(redis_datastore=REDIS_DATASTORE,
                    redis_key=work_key)
        records.append({'work':work})
    label_key = 'bf:Annotation:Facet:{0}s'.format(facet_name)
    msg = "Results {0} of {1} for Facet {2}".format(len(record_slice),
                                                    REDIS_DATASTORE.llen(listing_key),
                                                    facet_name)
    if REDIS_DATASTORE.exists(label_key):
        if REDIS_DATASTORE.type(label_key) == 'zset':
            msg = "{0} {1}".format(msg, facet_item)
        else:
            msg = " {0} {1}".format(msg,    
                                    REDIS_DATASTORE.hget(label_key, facet_item))
    else:
        msg = "{0} of {1}".format(msg, facet_item)
    return direct_to_template(request,
                              'discovery/app.html',
                              {'app': APP,
                               'example':{},
                               'feedback_form':FeedbackForm({'subject':'Discovery Facet Display'}),
                               'feedback_context':request.get_full_path(),
                               'institution': INSTITUTION,
                               'facet_list': None,
                               'message': msg,
                               'pagination':pagination,
                               'results':records,
                               'search_form': SearchForm(),
                               'search_query': None,
                               'user': None})

                              

    return HttpResponse("In facet detail key={0}\n{1}".format(redis_key,records))

def language_facet(request, name):
    return facet_detail(request, 'Language', name)

def location_facet(request, name):
    raise Http404

    

def facet_summary(request,facet_name):
    """
    Displays A general facet with all of its's items
    """
    redis_key = "bf:Annnotation:Facet:{0}s".format(facet_name)
    if not REDIS_DATASTORE.exists(redis_key):
        raise Http404
    return HttpResponse("In facet_summary, Facet = {0}".format(redis_key))
    

def instance(request,redis_id):
    """
    Instance view for the discovery app

    :param request: HTTP Request
    :param redis_id": Redis integer for the Instance
    """
    redis_key = "bf:Instance:{0}".format(redis_id)
    if REDIS_DATASTORE.exists(redis_key):
        instance = Instance(redis_datastore=REDIS_DATASTORE,
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
    redis_key = "bf:Person:{0}".format(redis_id)
    if REDIS_DATASTORE.exists(redis_key):
        person = Person(redis_datastore=REDIS_DATASTORE,
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

@json_view
def person_json_ld(request, redis_id):
    """
    Person JSON-LD view for the discovery app

    :param request: HTTP Request
    :param redis_id": Redis integer for the Person
    """
    redis_key = "bibframe:Person:{0}".format(redis_id)
    if REDIS_DATASTORE.exists(redis_key):
        json_linked_data = get_json_linked_data(redis_datastore=REDIS_DATASTORE,
                                                redis_key=redis_key)
        for work_key in list(REDIS_DATASTORE.smembers("{0}:rda:isCreatorPersonOf")):
            work_url = "http://{0}/apps/discovery/Work/{1}".format(request.get_host(), 
                                                                   work_key.split(":")[-1])
            if json_linked_data.has_key('rda:isCreatorPersonOf'):
                json_linked_data['rda:isCreatorPersonOf'].append(work_url)
            else:
                json_linked_data['rda:isCreatorPersonOf'] = [work_url,]
    return json_linked_data

@json_view
def search(request):
    """
    JSON-based search api for external calls into the discovery app
    """
    query = request.POST.get('q')
    type_of = request.POST.get('q_type')
    if len(query) > 0:
        bibframe_search = BIBFRAMESearch(q=query,
                                         type_of=type_of,
                                         redis_datastore=REDIS_DATASTORE)
        bibframe_search.run()
        search_results = json.loads(bibframe_search.__json__())
        return search_results
    else:
        return {'works':[]}




def bibframe_router(request,
                    entity_name,
                    redis_id):
    """View routes based on the Bibframe class and Redis id

    Parameters:
    entity_name -- Bibframe class anem
    redis_id -- Redis integer for the Bibframe entity
    """
    bibframe_key = "bf:{0}:{1}".format(entity_name,
                                       redis_id)
    if not REDIS_DATASTORE.exists(bibframe_key):
        bibframe_key = "bf:{0}:{1}".format(entity_name.title(),
                                           redis_id)
        if not REDIS_DATASTORE.exists(bibframe_key):
            raise Http404
    if CREATIVE_WORK_CLASSES.count(entity_name) > 0:
        cw_class = getattr(bibframe.models,
                           entity_name)
        if cw_class is None:
            cw_class = getattr(bibframe.models,
                               entity_name.title())
                               
        creative_work = cw_class(
            redis_datastore=REDIS_DATASTORE,
            redis_key=bibframe_key)
        return direct_to_template(request,
                    'discovery/work.html',
                  {'app': APP,
                   'creative_work':creative_work,
                   'feedback_form':FeedbackForm({'subject':'Discovery App Creative Work'}),
                   'feedback_context':request.get_full_path(),
                   'institution': INSTITUTION,
                   'search_form': SearchForm(),
                   'user':None})
    elif entity_name == 'Instance':
        instance = Instance(
            redis_datastore=REDIS_DATASTORE,
            redis_key=bibframe_key)
    
        return direct_to_template(request,
                      'discovery/instance.html',
                  {'app': APP,
                   'feedback_form':FeedbackForm({'subject':'Discovery App Instance'}),
                   'feedback_context':request.get_full_path(),
                   'instance':instance,
                   'institution': INSTITUTION,
                   'search_form': SearchForm(),
                   'user':None})
    elif entity_name == 'Organization':
        organization = bibframe.models.Organization(
            redis_datastore=REDIS_DATASTORE,
            redis_key=bibframe_key)
        return render(request,
                      'discovery/organization.html',
                      {'app': APP,
                       'feedback_form':FeedbackForm({'subject':'Discovery App Organization'}),
                       'feedback_context':request.get_full_path(),
                       'organization': organization,
                       'search_form': SearchForm(),
                       'user': None})
    elif entity_name == 'Person':
        person = bibframe.models.Person(
            redis_datastore=REDIS_DATASTORE,
            redis_key=bibframe_key)
        return render(request,
                      'discovery/person.html',
                      {'app': APP,
                       'feedback_form':FeedbackForm({'subject':'Discovery App Organization'}),
                       'feedback_context':request.get_full_path(),
                       'person': person,
                       'search_form': SearchForm(),
                       'user': None})
        
    return HttpResponse("{0} exits {1}".format(
        bibframe_key,
        REDIS_DATASTORE.exists(bibframe_key)))
    


@json_view
def bibframe_json_router(request,
                         entity_name,
                         redis_id):
    """View json ld routes based on the Bibframe class and Redis id

    Parameters:
    entity_name -- Bibframe class anem
    redis_id -- Redis integer for the Bibframe entity
    """
    bibframe_key = "bf:{0}:{1}".format(entity_name,
                                       redis_id)
    
    if not REDIS_DATASTORE.exists(bibframe_key):
        raise Http404
##    cw_class = getattr(bibframe.models,
##                       entity_name)
##    
##    bf_entity = cw_class(redis_datastore=REDIS_DATASTORE,
##                         redis_key=bibframe_key)
    json_linked_data = get_json_linked_data(redis_datastore=REDIS_DATASTORE,
                                            redis_key=bibframe_key)
    return json_linked_data
    
