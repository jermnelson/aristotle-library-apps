"""
 :mod:`discovery_extras` Discovery Application specific tags
"""
__author__ = 'Jeremy Nelson'
import aristotle.settings as settings
import redis
from django.template import Context,Library,loader
from django.utils import simplejson as json
from django.utils.safestring import mark_safe
from discovery.app_settings import CARRIER_TYPE_GRAPHICS
from aristotle.settings import INSTITUTION,ANNOTATION_REDIS,AUTHORITY_REDIS
from aristotle.settings import INSTANCE_REDIS,OPERATIONAL_REDIS,CREATIVE_WORK_REDIS

register = Library()

def get_creators(creative_work):
    """
    Returns generated html of Creators associated with the Creative Work

    :param creative_work: Creative Work
    :rtype: HTML or 0-length string
    """
    html_output = ''
    creator_template= loader.get_template('creator-icon.html')
    creators = list(CREATIVE_WORK_REDIS.smembers("{0}:rda:creator".format(creative_work.redis_key)))
    for key in creators:
        creator = AUTHORITY_REDIS.hgetall(key)
	redis_id = key.split(":")[-1]
	context = {'name':creator['rda:preferredNameForThePerson'],
                   'redis_id':redis_id}
	if 'rda:dateOfBirth' in creator:
            context['birth'] = creator['rda:dateOfBirth']
        if 'rda:dateOfDeath' in creator:
            context['death'] = creator['rda:dateOfDeath']
	html_output += creator_template.render(Context(context))
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


def get_title(creative_work):
    """
    Returns a Creative Work's title

    :param creative_work: Creative Work
    :rtype: string
    """
    try:
	preferred_title = creative_work.attributes['rda:Title']['rda:preferredTitleForTheWork']
        return mark_safe(preferred_title)
    except:
        return ''

register.filter('get_creators',get_creators)
register.filter('get_instances',get_instances)
register.filter('get_subjects',get_subjects)
register.filter('get_title',get_title)
