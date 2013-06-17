"""
 `prospector_extras` Module provides Prospector specific template tagsfor
 this consortium theme.

"""
__author__ = "Jeremy Nelson"

from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import stringfilter
from aristotle.settings import REDIS_DATASTORE

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
