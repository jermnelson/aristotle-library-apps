"""
 `colorado_college_extras` Module provides Colorado College specific template
 tags for White Whale-designned Discovery Layer
"""
__author__ = "Jeremy Nelson"

from django import template
from django.utils.safestring import mark_safe
from aristotle.settings import REDIS_DATASTORE
register = template.Library()

@register.filter(is_safe=True)
def get_facet(facet_key):
    "Returns accordion group based on template and redis-key"
    # Assume facet_key is sorted set
    facet_grp_template = template.loader.get_template('cc-facet-group')
    facet = {'label': facet_key.split(":")[-1],
             'items': []}
    facet['name'] = facet.get('label').lower().sub(" ","-")
    for item in REDIS_DATASTORE.zrevrange(facet_key,
                                          0,
                                          -1,
                                          withscores=True):
        item = {'label': item[0].split(":")[-1],
                'count': item[1]}
        facet['items'].append(item)
    return mark_safe(facet_grp_template.render(
        template.Context(facet)))
        
    
    
    
