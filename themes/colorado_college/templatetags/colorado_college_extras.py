"""
 `colorado_college_extras` Module provides Colorado College specific template
 tags for White Whale-designned Discovery Layer
"""
__author__ = "Jeremy Nelson"

from django import template
from django.utils.safestring import mark_safe
from bibframe.models import Instance
from aristotle.settings import REDIS_DATASTORE
register = template.Library()



@register.filter(is_safe=True)
def display_facet(facet):
    "Returns accordion group based on template and facet"
    expand = False
    if ["Access", "Format"].count(facet.name) > 0:
        expand = True
    facet_grp_template = template.loader.get_template('cc-facet-group.html')
    return mark_safe(facet_grp_template.render(
        template.Context({'expand': expand,
                          'facet':facet})))

@register.filter(is_safe=True)
def display_pagination(current_shard):
    "Filter generates pagination view based on the current shard"
    pagination_template = template.loader.get_template(
        'cc-pagination.html')
    current_int = int(current_shard.split(":")[-1])
    shard_pattern = current_shard[:-2]
    
    total_int = int(REDIS_DATASTORE.get('global {0}'.format(shard_pattern)))
    previous_int = current_int -1
    next_int = current_int +1
    if previous_int < 1:
        previous_int = 1
    shards = []
    for i in range(1, total_int):
        shards.append('{0}:{1}'.format(shard_pattern,
                                       i))
    previous_shard = '{0}:{1}'.format(shard_pattern,
                                     previous_int)
    
    
    next_shard = '{0}:{1}'.format(shard_pattern,
                                  next_int)
    return mark_safe(pagination_template.render(
        template.Context({'previous': previous_shard,
                          'next': next_shard,
                          'shard_num': current_int})))
         
@register.filter(is_safe=True)
def display_brief(work):
    "Returns CC version of a Brief summary based on White While DL design"
    work_template = template.loader.get_template(
        'cc-brief.html')
    title_entity = REDIS_DATASTORE.hget(work.title, 'label')
    if REDIS_DATASTORE.hexists(work.redis_key, "rda:isCreatedBy"):
        creators_keys = [REDIS_DATASTORE.hget(work.redis_key,
                                         "rda:isCreatedBy"),]
    else:
        creators_keys = list(REDIS_DATASTORE.smembers(
            "{0}:rda:isCreatedBy".format(work.redis_key)))
    creators = []
    for redis_key in creators_keys[:4]:
        creators.append({'id': redis_key.split(":")[-1],
                         'givenName': unicode(
            REDIS_DATASTORE.hget(redis_key, 'schema:givenName'),
            errors='ignore'),
                         'familyName': unicode(
            REDIS_DATASTORE.hget(redis_key, 'schema:familyName'),
            errors='ignore'),
                         'name':unicode(
             REDIS_DATASTORE.hget(redis_key,
                                  'rda:preferredNameForThePerson'),
             errors='ignore')})
                         
    context = template.Context({'creators': creators,
                                'title': title_entity,
                                'work': work}
                                )
    return mark_safe(work_template.render(context))

@register.filter(is_safe=True)
def display_instances(work):
    "Generates a display of all of the instances for a work"
    work_instances_template = template.loader.get_template(
        'cc-work-instances.html')
    if type(work.hasInstance) == str:
        instances = [Instance(redis_key=work.hasInstance,
                              redis_datastore=REDIS_DATASTORE),]
    context =  template.Context({'instances': instances})
    return mark_safe(work_instances_template.render(context))

@register.filter(is_safe=True)
def display_instance_summary(instance):
    "Generates a summary of an Instance"
    output = "This is {0}".format(getattr(instance,
                                          'rda:carrierTypeManifestation'))
    if hasattr(instance, 'isbn'):
        output += " with an ISBN of {0}.".format(instance.isbn)
    if instance.language is not None:
        output += " Language published in {0}".format(instance.language)
    if hasattr(instance, 'rda:dateOfPublicationManifestation'):
        output += " Published date of {0}".format(
            getattr(instance,
                    'rda:dateOfPublicationManifestation'))
    return mark_safe(output)
    

@register.filter(is_safe=True)
def get_facet(facet):
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
        
    
    
    
