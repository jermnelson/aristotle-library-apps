"""
 `prospector_extras` Module provides Prospector specific template tagsfor
 this consortium theme.

"""
__author__ = "Jeremy Nelson"

import json
from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import stringfilter
from aristotle.settings import REDIS_DATASTORE

from themes.prospector.redis_helpers import update_institution_count

register = template.Library()

@register.filter(is_safe=True)
def get_featured_instances(num_items=5):
    """
    Returns Creative Works that display as a listing of
    BIBFRAME Instances, will display CoverArt if available

    :param num_items: Number of featured items
    """
    featured_instances = []
    featured_keys = REDIS_DATASTORE.smembers('prospector:featured')
    for key in featured_keys:
        info = {'redis_key': key}
        featured_instances.append(info)
    featured_items_template = template.loader.get_template(
        'discovery/carl-featured-instances.html')
    return mark_safe(featured_items_template.render(template.Context({
        'instances': featured_instances})))

@register.filter(is_safe=True)
def get_news(num_items=5):
    """
    Returns a rendered list of news items with a default
    number of five news items.
    
    :param num_items: The number of news items to display
    """
    news = REDIS_DATASTORE.zrange("prospector:news",
                         -(int(num_items)),
                         -1)
    news_template = template.loader.get_template('carl-news.html')
    return mark_safe(news_template.render(template.Context({'news':news})))

@register.filter(is_safe=True)
def get_prospector_bar_chart(app=None):
    "Returns a javascript for a Canvas.js bar chart of Prospector Holdings"
    js_str = "var ctx=$('#prospector-rlsp-bar').get(0).getContext('2d');"
    data = {'labels':[],
            'data':[]}
    for row in  REDIS_DATASTORE.zrevrange('prospector-holdings',
                                          0,
                                          -1,
                                          withscores=True):
        if float(row[1]) > 0:
            org_key = row[0]
            data['labels'].append(REDIS_DATASTORE.hget(org_key, 'label'))
            data['data'].append(str(row[1]))
    js_str += """var data={{ labels: ["{0}"],""".format('","'.join(data['labels']))
    js_str += """datasets: [ {{ fillColor : "rgba(151,187,205,0.5)",
                               strokeColor : "rgba(151,187,205,1)",
                               data : [{0}]}}]}};""".format(','.join(data['data']))
    js_str += "new Chart(ctx).Bar(data, {scaleShowLabel: true});"
    return mark_safe(js_str)

@register.filter(is_safe=True)
def get_prospector_data(app=None):
    "Returns Google Charts string of Prospector Holdings"
    # update_institution_count()
    js_str = ''
    #! THIS OPERATION SHOULD BE CACHED
    for row in  REDIS_DATASTORE.zrevrange('prospector-holdings',
                                          0,
                                          -1,
                                          withscores=True):
        org_key = row[0]
        if int(row[1]) < 1:
            continue
        library_info = [REDIS_DATASTORE.hget(org_key, 'label'),
                        REDIS_DATASTORE.scard(
                            "{0}:bf:Books".format(org_key)),
                        REDIS_DATASTORE.scard(
                            "{0}:bf:MovingImage".format(org_key)),
                        REDIS_DATASTORE.scard(
                            "{0}:bf:MusicalAudio".format(org_key)),
                        row[1] # Total Holdings
                        ]
        js_str += '["{0}",{1}],\n'.format(library_info[0],
                                          ','.join([str(i)
                                                    for i in library_info[1:]]))
    js_str = js_str[:-2] # Removes trailing comma
    return mark_safe(js_str)
        
                
            
            
            
            
        

@register.filter(is_safe=True)
def get_facet(facet):
    """Returns generated html for a CARL Prospector Facet

    Parameters:
    facet -- facet
    """
    facet_template = template.loader.get_template('carl-facet.html')
    return mark_safe(facet_template.render(template.Context({'facet':facet})))
##register.filter('get_featured_instances',
##                get_featured_instances)
##register.filter('get_news',
##                get_news)
