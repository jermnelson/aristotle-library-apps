__author__ = "Jeremy Nelson"
import json
import os
from aristotle.settings import AUTHORITY_REDIS, PROJECT_HOME
from bibframe.models import Organization
from organization_authority.redis_helpers import get_or_add_organization


def load_prospector_orgs(authority_ds=AUTHORITY_REDIS):
    """Function loads Prospector Libraries into RLSP

    Parameters:
    authority_ds -- Authority Datastore, defaults to settings
    """
    prospector_orgs = json.load(open(os.path.join(PROJECT_HOME,
                                                  "themes",
                                                  "prospector", 
                                                  "fixures",
                                                  "prospector-orgs.json"),
                                      "rb"))
    for code, info in prospector_orgs.iteritems():
        info['prospector-abbv'] = code
        organization = get_or_add_organization(info, authority_ds)
        authority_ds.hset('prospector-institution-codes', 
                          info.get('prospector-id'),
                          organization.redis_key)

def add_ils_location(place_key, code_list, authority_redis):
      if len(code_list) < 1:
          pass
      elif len(code_list) == 1:                     
          authority_redis.hset(place_key, 
                               'ils-location-code', code_list[0])
      else:
          authority_redis.sadd('{0}:ils-location-codes'.format(place_key),
                               code_list)


def add_place(institution_redis_key, authority_redis):
    place_base ="{0}:schema:Place".format(institution_redis_key) 
    place_key = "{0}:{1}".format(
            place_base,
            authority_redis.incr('global {0}'.format(place_base)))
    return place_key

    
def load_institution_places(prospector_code,
                            json_filename,
                            authority_ds=AUTHORITY_REDIS):
    """Function loads an Institution's Places codes into RLSP

    Parameters:
    prospector_code -- Prospector code
    json_filename -- Filename of an institution's places encoded in JSON
    """
    institution_key = authority_ds.hget('prospector-institution-codes',
                                        prospector_code)
    places = json.load(os.path.join(PROJECT_HOME,
                                    "themes",
                                    "prospector", 
                                    "fixures",
                                    json_filename))
    for name, info in places.iteritems():
        place_key = add_place(institution_key, authority_redis)
        authority_redis.hset(place_key, 'name', name)
        # Should be the standard case, a listing of ils codes associated 
        if type(info) == list:
            add_ils_location(place_key, info, authority_redis)
        elif type(info) == dict:
            sub_place_keys = []
            for key, value in info.iteritems():
                sub_place_key = add_place(institution_key, authority_redis)
                authority_redis.hset(sub_place_key, 'name', key)
                authority_redis.hset(sub_place_key, 'schema:containedIn', place_key)
                add_ils_location(sub_place_key, info, authority_redis)
                sub_place_keys.append(sub_place_key)
            if len(sub_place_keys) < 1:
                pass
            elif len(sub_place_keys) == 1:
                authority_redis.hset(place_key, "contains", sub_place_keys[0])
            else:
                authority_redis.sadd('{0}:contains'.format(place_key), 
                                     sub_place_keys)
