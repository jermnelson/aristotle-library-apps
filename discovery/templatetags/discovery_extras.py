"""
 :mod:`discovery_extras` Discovery Application specific tags
"""
__author__ = 'Jeremy Nelson'
import aristotle.settings as settings
import redis
import xml.etree.ElementTree as etree
from bibframe.bibframe_models import CreativeWork,Instance
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
    work_key = instance.attributes.get('bibframe:CreativeWork')
    info.append(('Creative Work',
	         '''<a href="/apps/discovery/work/{0}/">Link <i class="icon-share"></i></a>'''.format(work_key.split(":")[-1])))
    print("INFO is {0}".format(info))
    info.append(('Format',instance.attributes.get('rda:carrierTypeManifestation')))
    creator_keys = CREATIVE_WORK_REDIS.smembers("{0}:rda:creator".format(work_key))
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
    info.append((label,creator_dd))
    print("After creator: {0}".format(info))
    facets = INSTANCE_REDIS.smembers("{0}:Annotations:facets".format(instance.redis_key))
    for key in facets:
        if key.startswith('bibframe:Annotation:Facet:Access'):
	    info.append(('Access',key.split(":")[-1]))
        if key.startswith('bibframe:Annotation:Facet:Location'):
	    location = ANNOTATION_REDIS.hget('bibframe:Annotation:Facet:Locations',
		                             key.split(":")[-1])
	    info.append(('Location in Library',location))
    identifiers = instance.attributes['rda:identifierForTheManifestation']
    if identifiers.has_key('lccn'):
        info.append(('LOC Call Number',identifiers.get('lccn')))
    if identifiers.has_key('local'):
        info.append(('Local Call Number',identifiers.get('local')))
    if identifiers.has_key('sudoc'):
        info.append(('Government Call Number',identifers.get('sudoc')))
    if identifiers.has_key('ils-bib-number'):
        info.append(('Legacy ILS number',identifiers.get('ils-bib-number')))
    info = sorted(info)
    html_output = ''
    for row in info:
        html_output += '<dt>{0}</dt><dd>{1}</dd>'.format(row[0],row[1])
    return mark_safe(html_output)

def get_creators(bibframe_entity):
    """
    Returns generated html of Creators associated with the Creative Work

    :param bibframe_entity: Creative Work or Instance
    :rtype: HTML or 0-length string
    """
    html_output = ''
    creator_template= loader.get_template('creator-icon.html')
    if type(bibframe_entity) == Instance:
        redis_key = bibframe_entity.attributes.get('bibframe:CreativeWork')
    else:
        redis_key = bibframe_entity.redis_key
    creators = list(CREATIVE_WORK_REDIS.smembers("{0}:rda:creator".format(redis_key)))
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
	context = {'image':person.attributes.get('image','creative_writing_48x48.png'),
		   'instances':instances,
                   'redis_id':wrk_key.split(":")[-1],
		   'title':unicode(CREATIVE_WORK_REDIS.hget('{0}:rda:Title'.format(wrk_key),
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
    if ["birth","death"].count(type_of) < 1:
        raise ValueError("get_date's type_of should 'birth' or 'death', got {0}".format(type_of))
    if type_of == 'birth':
        output = person.attributes.get('rda:dateOfBirth','')
    else:
        output = person.attributes.get('rda:dateOfDeath','')
    return mark_safe(output)


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
    carrier_type = instance.attributes['rda:carrierTypeManifestation']
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
        carrier_type = instance['rda:carrierTypeManifestation']
        context = {'graphic':CARRIER_TYPE_GRAPHICS.get(carrier_type,"publishing_48x48.png"),
		   'name':carrier_type,
		   'redis_id':key.split(":")[-1]}
	html_output += instance_template.render(Context(context))
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
    output = unicode(person.attributes.get('rda:preferredNameForThePerson',''),errors='ignore')
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
    facets = list(CREATIVE_WORK_REDIS.smembers("{0}:Annotations:facets".format(creative_work.redis_key)))
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
	if bibframe_entity.attributes.has_key('rda:Title'):
	    preferred_title = bibframe_entity.attributes['rda:Title']['rda:preferredTitleForTheWork']
	elif bibframe_entity.attributes.has_key('bibframe:CreativeWork'):
	    work_key = bibframe_entity.attributes.get('bibframe:CreativeWork')
	    preferred_title = CREATIVE_WORK_REDIS.hget('{0}:rda:Title'.format(work_key),
                                                       'rda:preferredTitleForTheWork')
        return mark_safe(preferred_title)
    except:
        return ''

register.filter('about_instance',about_instance)
register.filter('get_creators',get_creators)
register.filter('get_creator_works',get_creator_works)
register.filter('get_date',get_date)
register.filter('get_ids',get_ids)
register.filter('get_image',get_image)
register.filter('get_instances',get_instances)
register.filter('get_location',get_location)
register.filter('get_name',get_name)
register.filter('get_subjects',get_subjects)
register.filter('get_title',get_title)
