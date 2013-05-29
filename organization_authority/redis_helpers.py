"""
 :mod:`redis_helpers` Helper Classes and Functions for managing BIBFrAME 
 Organization Authorities in the Redis Library Services Platform
"""
__author__ = "Jeremy Nelson"
import re
from bibframe.models import Organization
from person_authority.redis_helpers import process_name
from aristotle.settings import AUTHORITY_REDIS, CREATIVE_WORK_REDIS, INSTANCE_REDIS


PUNCTUATION_RE = re.compile(r"[^!-~]|[.,;:]")

def add_organization(name_metaphone_keys,
		     org_attributes,
                     authority_redis=AUTHORITY_REDIS):
    """Function adds a BIBFRAME Organization to RLSP

    Function takes a Redis authority instance, the organization's name metaphone
    keys and the organization's attributes to create a BIBFRAME organization
    entity in the RLSP.

    Parameters:
    authority_redis -- Redis Authority Datastore
    name_metaphones_keys -- A list of the Organization's Name as metaphone keys
    org_attributes -- Dict of organization's properties 
    """
    new_organization = Organization(primary_redis=authority_redis)
    for key, value in org_attributes.iteritems():
        setattr(new_organization, key, value)
    new_organization.save()
    for metaphone in name_metaphone_keys:
        authority_redis.sadd(metaphone, new_organization.redis_key)
    return new_organization


def get_or_add_organization(org_attributes,
                            authority_redis=AUTHORITY_REDIS):
    """
    Function takes a dict of an organization's attributes and either returns an existing
    Organization or creates a new organization based on similarity metric.

    :param org_attributes:
    :param authority_redis: Redis BIBFRAME Authority instance
    """
    name_metaphones, name_metaphone_keys, org_keys = [], [], []
    normed_location_key, place_keys = None, []
    if 'label' in org_attributes:
        raw_name = org_attributes.get('label')
        name_metaphones = process_name(raw_name)
        name_metaphone_keys = ["organization-metaphone:{0}".format(x) for x in name_metaphones]
    existing_org_keys = authority_redis.sinter(name_metaphone_keys)
    if len(existing_org_keys) == 0:
        return add_organization(name_metaphone_keys, 
                                org_attributes, 
                                authority_redis)
    else:
        return Organization(redis_key=existing_org_keys[0],
                            primary_redis=authority_redis)
        	




