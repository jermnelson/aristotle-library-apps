"""
 :mod:`discovery_extras` Discovery Application specific tags
"""
__author__ = 'Jeremy Nelson'
import aristotle.settings as settings
import redis, inspect
import xml.etree.ElementTree as etree
from bibframe.models import Work,Instance,Person,Holding
from django.template import Context,Library,loader
from django.utils import simplejson as json
from django.utils.safestring import mark_safe
from discovery.app_settings import CARRIER_TYPE_GRAPHICS
from aristotle.settings import INSTITUTION,ANNOTATION_REDIS,AUTHORITY_REDIS
from aristotle.settings import INSTANCE_REDIS,OPERATIONAL_REDIS,CREATIVE_WORK_REDIS

register = Library()

def about_instance(instance):
    """
    Returns HTML for the about section in the Instance view

    :param instance:
    :rtype: HTML or -0-length string
    """
    info = []
    if hasattr(instance,'rda:carrierTypeManifestation'):
        info.append(('Format',getattr(instance,'rda:carrierTypeManifestation')))
    if CREATIVE_WORK_REDIS.hexists(instance.instanceOf,'rda:isCreatedBy'):
        creator_keys = [CREATIVE_WORK_REDIS.hget(instance.instanceOf,'rda:isCreatedBy'),]
    else:
        creator_keys = CREATIVE_WORK_REDIS.smembers("{0}:rda:isCreatedBy".format(instance.instanceOf))
    creator_dd = ''
    for key in creator_keys:
	creator_info = AUTHORITY_REDIS.hgetall(key)
	name = unicode(creator_info.get('rda:preferredNameForThePerson'),errors='ignore')
	creator_dd += '''<a href="/apps/discovery/authority/person/{0}/">
	<i class="icon-user"></i> {1}</a>'''.format(key.split(":")[-1],
    name)
	if 'rda:dateOfBirth' in creator_info:
	    creator_dd += '({0}-'.format(creator_info.get('rda:dateOfBirth'))
	if 'rda:dateOfDeath' in creator_info:
            creator_dd += '{0})'.format(creator_info.get('rda:dateOfDeath'))
	creator_dd += '<br/>'
    if len(creator_keys) > 1:
        label = 'Creators'
    else:
        label = 'Creator'
    if len(creator_dd) > 0:
        info.append((label,creator_dd))
    for type_of in ['issn','isbn']:
	number_key = '{0}:rda:identifierForTheManifestation:{1}'.format(instance.redis_key,
			                                                type_of)
	if INSTANCE_REDIS.exists(number_key):
	    number_ids = list(INSTANCE_REDIS.smembers(number_key))
            info.append((type_of.upper(),' '.join(number_ids)))
    facets = INSTANCE_REDIS.smembers("{0}:Annotations:facets".format(instance.redis_key))
    for key in facets:
        if key.startswith('bibframe:Annotation:Facet:Access'):
	    info.append(('Access',key.split(":")[-1]))
        if key.startswith('bibframe:Annotation:Facet:Location'):
	    location = ANNOTATION_REDIS.hget('bibframe:Annotation:Facet:Locations',
		                             key.split(":")[-1])
	    info.append(('Location in Library',location))
    #identifiers = getattr(instance,'rda:identifierForTheManifestation')
    for name in dir(instance):
       value = getattr(instance,name)
       if name.startswith("__") or name.find('redis') > -1:
           continue
       if inspect.ismethod(getattr(instance,name)):
           continue
       
       if OPERATIONAL_REDIS.hexists('bibframe:vocab:Instance:labels',
                                    name):
           if value is not None:
               label = OPERATIONAL_REDIS.hget('bibframe:vocab:Instance:labels',
                                               name)
               instance_attribute = getattr(instance,name)
               if type(instance_attribute) == set:
                   for row in list(instance_attribute):
                       info.append((label,row))
               elif type(instance_attribute) == dict:
                   for k,v in instance_attribute.iteritems():
                       info.append((k,v))
               elif name == 'instanceOf':
                   work_key = instance.instanceOf
                   info.append((name,
                                '''<a href="/apps/discovery/work/{0}/">{1} <i class="icon-share"></i></a>'''.format(work_key.split(":")[-1],
                                                                                                                    work_key)))

               else:
                   info.append((label,instance_attribute))
       else:
           if type(value) == dict:
               for k,v in value.iteritems():
                   info.append((k,v))
           if name == 'rda:uniformResourceLocatorItem':
               info.append((name,'<a href="{0}">{1}</a>'.format(value,value)))
           else:
               info.append((name,getattr(instance,name)))
       
    #if identifiers.has_key('lccn'):
    #    info.append(('LOC Call Number',identifiers.get('lccn')))
    #if identifiers.has_key('local'):
    #    info.append(('Local Call Number',identifiers.get('local')))
    #if identifiers.has_key('sudoc'):
    #    info.append(('Government Call Number',identifiers.get('sudoc')))
    #if identifiers.has_key('ils-bib-number'):
    #    info.append(('Legacy ILS number',identifiers.get('ils-bib-number')))
    info = sorted(info)
    # Publishing Information
    #if 'rda:dateOfPublicationManifestation' in instance:
    #    info.append(('Published',instance.attributes['rda:dateOfPublicationManifestation']))
    html_output = ''
    for row in info:
        html_output += '<dt>{0}</dt><dd>{1}</dd>'.format(row[0],row[1])
    return mark_safe(html_output)

def get_annotations(instance):
    """
    Returns Library Holdings and Facets

    """
    output = ''
    for redis_key in INSTANCE_REDIS.smembers('{0}:hasAnnotation'.format(instance.redis_key)):
        if redis_key.find('Facet') > -1:
            facet_info = redis_key.split(":")
            facet_url = "/apps/discovery/facet/{0}/{1}".format(facet_info[-2],
                                                               facet_info[-1])
        if redis_key.startswith('bibframe:Holding'):
            holdings_info = []
            for key,value in ANNOTATION_REDIS.hgetall(redis_key).iteritems():
                if OPERATIONAL_REDIS.hexists('bibframe:vocab:Holding:labels',
                                             key):
                    name = OPERATIONAL_REDIS.hget('bibframe:vocab:Holding:labels',key)
                else:
                    name = key
                if key != 'created_on' and key != 'annotates':
                    holdings_info.append({"name":name,
                                          "value":value})
            output += get_library_holdings(holdings_info)
        elif redis_key.find('Facet:Location') > -1:
            location_info = {'code':facet_info[-1],
                             'label': ANNOTATION_REDIS.hget('bibframe:Annotation:Facet:Locations',
                                                            facet_info[-1]),
                             'url':facet_url}
            location_template = loader.get_template('location-icon.html')
            output += location_template.render(Context({'location':location_info}))
        elif redis_key.find('Facet:Format') > -1:
            format_template = loader.get_template('carrier-type-icon.html')
            output += format_template.render(Context({'graphic':get_image(instance),
                                                      'label':facet_info[-1],
                                                      'url':facet_url}))
        
    return mark_safe(output)
      

def get_brief_heading(work):
    """
    Returns generated h4 for brief record view
    
    :param work: Creative Work
    :rtype: HTML or 0-length string
    """
    output = ''
    new_h4 = etree.Element('h4',attrib={'class':'media-heading'})
    new_a = etree.SubElement(new_h4,
		             'a',
		             attrib={'href':'/apps/discovery/work/{0}/'.format(work.redis_key.split(":")[-1])})
    new_a.text = get_title(work)
    output = etree.tostring(new_h4)
    return mark_safe(output)

def get_creators(bibframe_entity):
    """
    Returns generated html of Creators associated with the Creative Work

    :param bibframe_entity: Creative Work or Instance
    :rtype: HTML or 0-length string
    """
    html_output = ''
    creator_template= loader.get_template('creator-icon.html')
    if type(bibframe_entity) == Instance:
        redis_key = bibframe_entity.attributes.get('instanceOf')
    else:
        redis_key = bibframe_entity.redis_key
    if CREATIVE_WORK_REDIS.hexists(redis_key,"rda:isCreatedBy"):
        creators = [CREATIVE_WORK_REDIS.hget(redis_key,"rda:isCreatedBy"),]
    else:
        creators = list(CREATIVE_WORK_REDIS.smembers("{0}:rda:isCreatedBy".format(redis_key)))
    for key in creators:
        creator = AUTHORITY_REDIS.hgetall(key)
	redis_id = key.split(":")[-1]
	context = {'name':unicode(creator['rda:preferredNameForThePerson'],
		                  errors='ignore'),
                   'redis_id':redis_id}
	if 'rda:dateOfBirth' in creator:
            context['birth'] = creator['rda:dateOfBirth']
        if 'rda:dateOfDeath' in creator:
            context['death'] = creator['rda:dateOfDeath']
	html_output += creator_template.render(Context(context))
    return mark_safe(html_output)
    
def get_creator_works(person):
    """
    Returns HTML for each Creative Work associated with a creator

    :param person: Person
    :rtype: HTML or 0-length string
    """
    html_output = ''
    creative_works = AUTHORITY_REDIS.smembers("{0}:rda:isCreatorPersonOf".format(person.redis_key))
    if len(creative_works) > 0:
        html_output += '<h3>Total Works: {0}</h3>'.format(len(creative_works))
    work_template = loader.get_template('work-thumbnail.html')
    for wrk_key in creative_works:
        instance_keys = CREATIVE_WORK_REDIS.smembers("{0}:bibframe:Instances".format(wrk_key))
	instances = []
        for key in instance_keys:
            carrier_type = INSTANCE_REDIS.hget(key,'rda:carrierTypeManifestation')
            instances.append({'redis_id':key.split(":")[-1],
		              'carrier_type':carrier_type,
			      'graphic':CARRIER_TYPE_GRAPHICS.get(carrier_type,"publishing_48x48.png")})
        if hasattr(person,'image'):
            image = person.image
        else:
            image = 'creative_writing_48x48.png' 
	context = {'image':image,
		   'instances':instances,
                   'redis_id':wrk_key.split(":")[-1],
		   'title':unicode(CREATIVE_WORK_REDIS.hget('{0}:title'.format(wrk_key),
			                                    'rda:preferredTitleForTheWork'),
				   errors='ignore')}
	html_output += work_template.render(Context(context))
    return mark_safe(html_output)

def get_date(person,type_of):
    """
    Returns string of either a person's birth or death depending
    on the type_of value and if it exists or not.

    :param person: Person
    :param type_of: Type of date, should be "birth" or "death"
    """
    output = None
    if ["birth","death"].count(type_of) < 1:
        raise ValueError("get_date's type_of should 'birth' or 'death', got {0}".format(type_of))
    if type_of == 'birth' and hasattr(person,'rda:dateOfBirth'):
        output = getattr(person,'rda:dateOfBirth')
    elif hasattr(person,'rda:dateOfDeath'):
        output = getattr(person,'rda:dateOfDeath')
    if output is not None:
        return mark_safe(output)


def get_facet_url(facet_item):
    """
    Returns generated html of a Facet
    
    :param facet_item: FacetItem
    """
    facet_list = facet_item.redis_key.split(":")
    if len(facet_list) > 1:
        return mark_safe("/apps/discovery/facet/{0}/{1}".format(facet_list[-2],facet_list[-1]))

def get_ids(instance):
    """
    Returns generated html of the Instance's identifiers

    :param instance: Instance
    :rtype: HTML or 0-length string
    """
    html_output = ''
    identifiers = instance.attributes['rda:identifierForTheManifestation']
    if identifiers.has_key('lccn'):
        html_output += '<dt>LOC Call Number:</dt><dd>{0}</dd>'.format(identifiers.get('lccn'))
    if identifiers.has_key('local'):
	html_output += '<dt>Local Call Number:</dt><dd>{0}</dd>'.format(identifiers.get('local'))
    if identifiers.has_key('sudoc'):
        html_output += '<dt>Government Call Number:</dt><dd>{0}</dd>'.format(identifiers.get('sudoc'))
    if identifiers.has_key('ils-bib-number'):
        html_output += '<dt>Legacy ILS number:</dt><dd>{0}</dd>'.format(identifiers.get('ils-bib-number'))
    return mark_safe(html_output)

def get_image(instance):
    """
    Returns HTML img of an instance's graphic

    :param instance: Instance
    :rtype: HTML or 0-length string
    """
    if hasattr(instance,'rda:carrierTypeManifestation'):
        carrier_type = getattr(instance,'rda:carrierTypeManifestation')
        html_output = CARRIER_TYPE_GRAPHICS.get(carrier_type,"publishing_48x48.png")
        return mark_safe(html_output)


def get_instances(creative_work):
    """
    Returns generated html of the Creative Work's instances

    :param creative_work: Creative Work
    :rtype: HTML or 0-length string
    """
    html_output = ''
    instance_template = loader.get_template('instance-icon.html')
    instances = list(CREATIVE_WORK_REDIS.smembers("{0}:bibframe:Instances".format(creative_work.redis_key)))
    for key in instances:
	instance = INSTANCE_REDIS.hgetall(key)
        carrier_type = instance.get('rda:carrierTypeManifestation','Unknown')
        context = {'graphic':CARRIER_TYPE_GRAPHICS.get(carrier_type,"publishing_48x48.png"),
		   'name':carrier_type,
		   'redis_id':key.split(":")[-1]}
	html_output += instance_template.render(Context(context))
    return mark_safe(html_output)

def get_library_holdings(holdings_info):
    """
    Returns any library holdings for the instance

    :param holding_info: List of holdings info
    :rtype HTML or 0-length string
    """
    html_output = ''
    holding_template = loader.get_template('holding-icon.html')
    if len(holdings_info) > 0:
         context = {'holdings': holdings_info}
         html_output += holding_template.render(Context(context))
    return mark_safe(html_output)

def get_location(instance):
    """
    Returns Location of an Instance

    :param instance: Instance
    """
    location = ''
    facets = INSTANCE_REDIS.smembers("{0}:Annotations:facets".format(instance.redis_key))
    for key in facets:
        if key.startswith('bibframe:Annotation:Facet:Location'):
	    location = ANNOTATION_REDIS.hget('bibframe:Annotation:Facet:Locations',
		                             key.split(":")[-1])
    return mark_safe(location)


def get_name(person):
    """
    Returns a Person's name.

    :param person: Person
    :rtype: string
    """
    output = unicode(getattr(person,'rda:preferredNameForThePerson'),errors='ignore')
    return mark_safe(output)

def get_subjects(creative_work):
    """
    Returns generated html of subjects associated with the 
    Creative Work

    :param creative_work: Creative Work
    :rtype: HTML or 0-length string
    """
    html_output = ''
    #! Using LOC Facet as proxy for subjects
    facets = list(CREATIVE_WORK_REDIS.smembers("{0}:hasAnnotation".format(creative_work.redis_key)))
    for facet in facets:
        if facet.startswith("bibframe:Annotation:Facet:LOCFirstLetter"):
            subject_template = loader.get_template('subject-icon.html')
	    loc_key = facet.split(":")[-1]
	    context = {'name':ANNOTATION_REDIS.hget('bibframe:Annotation:Facet:LOCFirstLetters',
		                                    loc_key)}
	    html_output += subject_template.render(Context(context))
    return mark_safe(html_output)


def get_title(bibframe_entity):
    """
    Returns a Creative Work's title

    :param bibframe_entity: Bibframe Entity 
    :rtype: string
    """
    try:
	if hasattr(bibframe_entity,'title'):
            if bibframe_entity.title is not None:
	        preferred_title = unicode(bibframe_entity.title['rda:preferredTitleForTheWork'],
                                          encoding='utf-8',
                                          errors="ignore")
	if hasattr(bibframe_entity,'instanceOf'):
	    preferred_title = unicode(CREATIVE_WORK_REDIS.hget('{0}:title'.format(bibframe_entity.instanceOf),
                                                               'rda:preferredTitleForTheWork'),
                                      encoding='utf-8',
                                      errors="ignore")
        return mark_safe(preferred_title)
    except:
        return ''

register.filter('about_instance',about_instance)
register.filter('get_annotations',get_annotations)
register.filter('get_brief_heading',get_brief_heading)
register.filter('get_creators',get_creators)
register.filter('get_creator_works',get_creator_works)
register.filter('get_date',get_date)
register.filter('get_facet_url',get_facet_url)
register.filter('get_ids',get_ids)
register.filter('get_image',get_image)
register.filter('get_instances',get_instances)
register.filter('get_library_holdings',get_library_holdings)
register.filter('get_location',get_location)
register.filter('get_name',get_name)
register.filter('get_subjects',get_subjects)
register.filter('get_title',get_title)
