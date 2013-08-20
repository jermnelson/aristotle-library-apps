"""
 `colorado_college_extras` Module provides Colorado College specific template
 tags for White Whale-designned Discovery Layer
"""
__author__ = "Jeremy Nelson"

from django import template
from django.utils.safestring import mark_safe
from bibframe.models import Instance
from aristotle.settings import REDIS_DATASTORE
from discovery.forms import AnnotationForm
register = template.Library()


@register.filter(is_safe=True)
def author_of(person):
    "Returns div with a list of Works that the person is an author of"
    author_role_key = "{0}:resourceRole:aut".format(person.redis_key)
    if not REDIS_DATASTORE.exists(author_role_key):
        return mark_safe('')
    author_html = """<div class="alert alert-info alert-block">
    <h3>Author's Creative Works</h3><ul>"""
    for work_key in REDIS_DATASTORE.smembers(author_role_key):
        work_info = work_key.split(":")
        title_key = REDIS_DATASTORE.hget(work_key, 'title')
        title = REDIS_DATASTORE.hget(title_key, 'label')
        author_html += """<li>{0} <em><a href="/apps/discovery/{0}/{1}">{2}</a></li></em>
         """.format(work_info[1],
                    work_info[-1],
                    title)
    author_html += "</ul></div>"
    return mark_safe(author_html)
        
        

@register.filter(is_safe=True)
def display_facet(facet):
    "Returns accordion group based on template and facet"
    expand = False
    if ["access", "format"].count(facet.redis_id) > 0:
        expand = True
    facet_grp_template = template.loader.get_template('cc-facet-group.html')
    return mark_safe(facet_grp_template.render(
        template.Context({'expand': expand,
                          'facet':facet})))

@register.filter(is_safe=True)
def display_network_toolbar(redis_entity):
    """Returns a semantic and social network toolbar 

    Parameter:
    redis_entity -- BIBFRAME Entity
    """
    network_toolbar_template = template.loader.get_template(
        'cc-network-toolbar.html')
    return mark_safe(network_toolbar_template.render(
        template.Context({'entity': redis_entity})))

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
        creator = {'id': redis_key.split(":")[-1]}
        given_name = REDIS_DATASTORE.hget(redis_key, 'schema:givenName')
        if given_name is not None:
            creator['givenName'] = unicode(given_name, errors='ignore')
        family_name = REDIS_DATASTORE.hget(redis_key, 'schema:familyName')
        if family_name is not None:
            creator['familyName'] = unicode(family_name, errors='ignore')
        creator['name'] = unicode(REDIS_DATASTORE.hget(redis_key,
                                  'rda:preferredNameForThePerson'),
                                  errors='ignore')
        creators.append(creator)
        
                         
    context = template.Context({'creators': creators,
                                'title': title_entity,
                                'work': work}
                                )
    return mark_safe(work_template.render(context))

@register.filter(is_safe=True)
def display_person_dates(person):
    "Displays a person date of birth and death if present"
    date_html = """<dl class="dl-horizontal">"""
    if hasattr(person, 'rda:dateOfBirth'):
        date_html += "<dt>Date of Birth:</dt>"
        date_html += "<dd>{0}</dd>".format(getattr(person, 'rda:dateOfBirth'))
    if hasattr(person, 'rda:dateOfDeath'):
        date_html +=  "<dt>Date of Death:</dt>"
        date_html += "<dd>{0}</dd>".format(getattr(person, 'rda:dateOfDeath'))
    date_html += "</dl>"
    return mark_safe(date_html)

@register.filter(is_safe=True)
def display_instances(work):
    "Generates a display of all of the instances for a work"
    work_instances_template = template.loader.get_template(
        'cc-work-instances.html')
    instances = []
    instance_keys = list(REDIS_DATASTORE.smembers(
        "{0}:hasInstance".format(work.redis_key)))
    if len(instance_keys) < 1:
        instance_key = REDIS_DATASTORE.hget(work.redis_key,
                                             'hasInstance')
        if instance_key is not None:
            instance_keys.append(instance_key)
                
    for instance_key in instance_keys:
        instances.append(
            Instance(redis_key=instance_key,
                     redis_datastore=REDIS_DATASTORE))
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
def display_user_annotation_dialog(entity):
    "Displays a User Annotation dialog"
    user_dialog_template =  template.loader.get_template(
        'cc-user-annotation.html')
    context =  template.Context({'form': AnnotationForm(),
                                 'entity': entity})
    return mark_safe(user_dialog_template.render(context))
    
@register.filter(is_safe=True)
def get_creators(bibframe_entity):
    output = '<ul class="icons-ul">'
    if type(bibframe_entity) == Instance:
        redis_key = bibframe_entity.attributes.get('instanceOf')
    else:
        redis_key = bibframe_entity.redis_key
    if REDIS_DATASTORE.hexists(redis_key,"rda:isCreatedBy"):
        creators = [REDIS_DATASTORE.hget(redis_key,"rda:isCreatedBy"),]
    else:
        creators = list(REDIS_DATASTORE.smembers("{0}:rda:isCreatedBy".format(redis_key)))
        
    
    for i, key in enumerate(creators):
        creator_id = key.split(":")[-1]
        output += """<li><a href="/apps/discovery/Person/{0}">
<i class="icon-li icon-user"></i> {1}</a></li>""".format(
        key.split(":")[-1],
        REDIS_DATASTORE.hget(key,
                             'rda:preferredNameForThePerson'))
    output += "</ul>"
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
        
@register.filter(is_safe=True)
def get_work_total(work_name):
    work_key = "global bf:{0}".format(work_name)
    if REDIS_DATASTORE.exists(work_key):
        work_total = '{0:,}'.format(int(REDIS_DATASTORE.get(work_key)))
    else:
        work_total = 0
    return mark_safe(work_total)
    
    
