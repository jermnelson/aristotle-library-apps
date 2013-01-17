"""
 :mod:`redis_helpers` Helper Classes and Functions for managing BIBFrAME 
 Organization Authorities in the Redis Library Services Platform
"""
__author__ = "Jeremy Nelson"
import re
from bibframe.bibframe_models import Organization
from person_authority.redis_helpers import process_name
from aristotle.settings import AUTHORITY_REDIS, CREATIVE_WORK_REDIS, INSTANCE_REDIS


PUNCTUATION_RE = re.compile(r"[^!-~]|[.,;:]")

def add_organization(authority_redis,
		     name_metaphone_keys,
		     org_attributes):
    """
    Function takes a Redis authority instance, the organization's name metaphone
    keys and the organization's attributes to create a BIBFRAME organization
    entity in the RLSP.

    :param authority_redis:
    :param name_metaphones_keys:
    :param org_attributes:
    """
    new_organization = Organization(redis=authority_redis,
		                    attributes=org_attributes)
    new_organization.save()
    for metaphone_key in name_metaphone_keys:


def get_or_generate_organization(org_attributes,
		                 authority_redis=AUTHORITY_REDIS):
    """
    Function takes a dict of an organization's attributes and either returns an existing
    Organization or creates a new organization based on similarity metric.

    :param org_attributes:
    :param authority_redis: Redis BIBFRAME Authority instance
    """
    name_metaphones, name_metaphone_keys, org_keys = [], [], []
    normed_location_key, place_keys = None, []
    if 'rda:publishersName' in org_attributes:
        raw_name = org_attributes.get('rda:publishersName')
	name_metaphones = process_name(raw_name)
	name_metaphone_keys = ["organization-metaphone:{0}".format(x) for x in name_metaphones]
	org_keys = authority_redis.sinter(name_metaphone_keys)
    if 'rda:placeOfPublication' in org_attributes:
        # NEEDS Geographic Location Authority control, for now just upper-case each 
	# word in the place
	raw_location = org_attributes.get('rda:placeOfPublication')
	normed_location = PUNCTUATION_RE.sub("",raw_location).upper()
	normed_location_key = "normalized-location:{0}".format(normed_location)
    # Publisher's location exists, returns matches if all of the organization 
    # metaphone names match with the location key
    if normed_location_key is not None and len(org_keys) > 0:
        existing_org_keys = authority_redis.sinter(normed_location_key,org_keys)
	if len(existing_org_keys) == 0:
	    return Organization(redis_key=existing_org_keys[0],
			        redis=authority_redis)
        else:
            return None
	




