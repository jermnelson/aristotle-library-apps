__author__ = "Jeremy Nelson"
import datetime
import json
import os
import sys
from aristotle.settings import REDIS_DATASTORE, PROJECT_HOME
from bibframe.models import Organization
from organization_authority.redis_helpers import get_or_add_organization


def load_prospector_orgs(redis_datastore=REDIS_DATASTORE):
    """Function loads Prospector Libraries into RLSP

    Parameters:
    redis_datastore -- Redis Datastore, defaults to settings
    """
    prospector_orgs = json.load(open(os.path.join(PROJECT_HOME,
                                                  "themes",
                                                  "prospector", 
                                                  "fixures",
                                                  "prospector-orgs.json"),
                                      "rb"))
    if redis_datastore.exists('prospector-institution-codes'):
        return # These codes are already loaded into the RLSP
    for code, info in prospector_orgs.iteritems():
        info['prospector-abbv'] = code
        organization = get_or_add_organization(info, redis_datastore)
        redis_datastore.hset('prospector-institution-codes',
                             info.get('prospector-id'),
                             organization.redis_key)

def add_ils_location(place_key, code_list, REDIS_DATASTORE):
      if len(code_list) < 1:
          pass
      elif len(code_list) == 1:                     
          REDIS_DATASTORE.hset(place_key, 
                               'ils-location-code', code_list[0])
      else:
          REDIS_DATASTORE.sadd('{0}:ils-location-codes'.format(place_key),
                               code_list)


def add_place(institution_redis_key, REDIS_DATASTORE):
    place_base ="{0}:schema:Place".format(institution_redis_key) 
    place_key = "{0}:{1}".format(
            place_base,
            REDIS_DATASTORE.incr('global {0}'.format(place_base)))
    return place_key

def add_facet(facet_key,
              facet_sort_key,
              entity_key,
              redis_datastore=REDIS_DATASTORE):
    "Function adds facet to RLSP"
    redis_datastore.sadd(facet_key, entity_key)
    redis_datastore.zadd(facet_sort_key,
                         float(redis_datastore.scard(facet_key)),
                         facet_key)

def generate_facets(redis_datastore=REDIS_DATASTORE):
    "Function generates Prospector BIGFRAME facets"
    facet_keys = ['bf:Annotation:Facet:formats',
                  'bf:Annotation:Facet:LOCFirstLetters:sort',
                  'bf:Annotation:Facet:Languages',
                  'bf:Annotation:Facet:PublicationDate']
    # Generates Format Facet
    print("Starting post-hoc generation of Facets at {0}".format(
        datetime.datetime.utcnow().isoformat()))
    for i in xrange(1, int(redis_datastore.get('global bf:Instance'))):
        redis_key = "bf:Instance:{0}".format(i)
        carrier_type = redis_datastore.hget(redis_key,
                                            'rda:carrierTypeManifestation')
        if carrier_type is not None:
            format_facet = 'bf:Annotation:Facet:format:{0}'.format(
                carrier_type)
            add_facet(format_facet,
                      'bf:Annotation:Facet:formats',
                      redis_key,
                      redis_datastore)
            
        language_code = redis_datastore.hget(redis_key, 'language')
        if language_code is not None:
            language_facet = 'bf:Annotation:Facet:Language:{0}'.format(
                language_code)
            add_facet(language_facet,
                      'bf:Annotation:Facet:Languages',
                      redis_key,
                      redis_datastore)
        publication_date = redis_datastore.hget(redis_key,
                                                'rda:dateOfPublicationManifestation')
        if publication_date is not None:
            pub_date_facet = 'bf:Annotation:Facet:PublicationDate:{0}'.format(
                publication_date)
            add_facet(pub_date_facet,
                      'bf:Annotation:Facet:PublicationDate',
                      redis_key,
                      redis_datastore)
        if not i%100:
            sys.stderr.write(" {0}:{1} ".format(i, redis_key))
        else:
            sys.stderr.write(".")
    print("Finished post-hoc generation of Facets at {0}".format(
        datetime.datetime.utcnow().isoformat()))
                             
            
            
        


    
def load_institution_places(prospector_code,
                            json_filename,
                            authority_ds=REDIS_DATASTORE):
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
        place_key = add_place(institution_key, REDIS_DATASTORE)
        REDIS_DATASTORE.hset(place_key, 'name', name)
        # Should be the standard case, a listing of ils codes associated 
        if type(info) == list:
            add_ils_location(place_key, info, REDIS_DATASTORE)
        elif type(info) == dict:
            sub_place_keys = []
            for key, value in info.iteritems():
                sub_place_key = add_place(institution_key, REDIS_DATASTORE)
                REDIS_DATASTORE.hset(sub_place_key, 'name', key)
                REDIS_DATASTORE.hset(sub_place_key, 'schema:containedIn', place_key)
                add_ils_location(sub_place_key, info, REDIS_DATASTORE)
                sub_place_keys.append(sub_place_key)
            if len(sub_place_keys) < 1:
                pass
            elif len(sub_place_keys) == 1:
                REDIS_DATASTORE.hset(place_key, "contains", sub_place_keys[0])
            else:
                REDIS_DATASTORE.sadd('{0}:contains'.format(place_key), 
                                     sub_place_keys)

def update_institution_count(redis_datastore=REDIS_DATASTORE):
    "Updates consortium prospector-holdings Bibframe annotation"
    for org_code, org_key in redis_datastore.hgetall(
        'prospector-institution-codes').iteritems():
        org_holding_key = '{0}:resourceRole:own'.format(org_key)
        score = float(redis_datastore.scard(org_holding_key))
        redis_datastore.zadd('prospector-holdings',
                             score,
                             org_key)
        for instance_key in redis_datastore.smembers(org_holding_key):
            work_key = redis_datastore.hget(instance_key, 'instanceOf')
            if work_key.startswith('bf:Book'):
                redis_datastore.sadd("{0}:bf:Books".format(org_key),
                                     work_key)
            if work_key.startswith('bf:MovingImage'):
                redis_datastore.sadd("{0}:bf:MovingImages".format(org_key),
                                     work_key)
            if work_key.startswith('bf:MusicalAudio'):
                redis_datastore.sadd("{0}:bf:MusicalAudios".format(org_key),
                                     work_key)
            
                      
    


    
