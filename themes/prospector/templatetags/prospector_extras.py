"""
 `prospector_extras` Module provides Prospector specific template tagsfor
 this consortium theme.

"""
__author__ = "Jeremy Nelson"

from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import stringfilter
from aristotle.settings import OPERATIONAL_REDIS as OPS_DS
from aristotle.settings import CREATIVE_WORK_REDIS as CW_DS
from aristotle.settings import INSTANCE_REDIS as INSTANCE_DS

register = template.Library()

@register.filter(is_safe=True)
def get_featured_instances(num_items=5):
    """
    Returns Creative Works that display as a listing of
    BIBFRAME Instances, will display CoverArt if available

    :param num_items: Number of featured items
    """
    featured_instances = []
    featured_keys = OPS_DS.smembers('prospector:featured')
    for key in featured_keys:
        info = {'redis_key': key}
        INSTANCE_DS    
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
    news = OPS_DS.zrange("prospector:news",
                         -(int(num_items)),
                         -1)
    news_template = template.loader.get_template('carl-news.html')
    return mark_safe(news_template.render(template.Context({'news':news})))

##register.filter('get_featured_instances',
##                get_featured_instances)
##register.filter('get_news',
##                get_news)
