"""
 :mod:`redis_helpers` Person Authority Helper Utilities
"""
__author__ = "Jeremy Nelson"
from bibframe.models import Person

import aristotle.lib.metaphone as metaphone
from bibframe.redis_helpers import get_brief
from title_search.redis_helpers import STOPWORDS
from aristotle.settings import AUTHORITY_REDIS, CREATIVE_WORK_REDIS, INSTANCE_REDIS

def add_person(authority_redis,
               person_attributes,
               person_metaphones_keys):
    """
    Function adds a bibframe_models.Person to authority datastore

    :param authority_redis: Authority Redis datastore
    :param person_metaphones_keys: Metaphones for Person's name
    """
    new_person = Person(primary_redis=authority_redis)
    for key, value in person_attributes.iteritems():
        setattr(new_person,key,value)
    new_person.save()
    for metaphone in person_metaphones_keys:
        authority_redis.sadd(metaphone,new_person.redis_key)
    
    if hasattr(new_person,'rda:dateOfBirth'):
        raw_dob = person_attributes.get('rda:dateOfBirth')
        authority_redis.sadd('person-dob:{0}'.format(raw_dob),
                             new_person.redis_key)
    if hasattr(new_person,'rda:dateOfDeath'):
        raw_dod = person_attributes.get('rda:dateOfDeath')
        authority_redis.sadd('person-dod:{0}'.format(raw_dod),
                             new_person.redis_key)
    return new_person


def get_person(person_redis_key,
               authority_redis):
    """
    Function gets a bibframe_models.Person to authority datastore

    :param person_redis_key: Person Redis Key
    :param authority_redis: Authority Redis datastore
    """
    existing_person = Person(primary_redis=authority_redis,
                             redis_key=person_redis_key)
    return existing_person
                             
    

def get_or_generate_person(person_attributes,authority_redis):
    """
    Method either returns a new Person or an existing Person based
    on a similarity metric.

    :param person_attributes: Person attributes in a dict
    :param authority_redis: MARCR Authority Redis datastore
    """
    person_metaphones,person_metaphones_keys,person_keys = [],[],[]
    dob_keys,dod_keys = [],[]
    if person_attributes.has_key("rda:preferredNameForThePerson"):
        raw_name = person_attributes.get("rda:preferredNameForThePerson")
        person_metaphones = process_name(raw_name)
        person_metaphones_keys = ["person-metaphones:{0}".format(x) for x in person_metaphones]
        person_keys = authority_redis.sinter(person_metaphones_keys)
    if person_attributes.has_key("rda:dateOfBirth"):
        raw_dob = person_attributes.get('rda:dateOfBirth')
        dob_keys = authority_redis.smembers('person-dob:{0}'.format(raw_dob))
    if person_attributes.has_key("rda:dateOfDeath"):
        raw_dod = person_attributes.get('rda:dateOfDeath')
        dod_keys = authority_redis.smembers('person-dod:{0}'.format(raw_dod))
    # No match on names, assume Person is not in the datastore and add to datastore
    if len(person_keys) <= 0:
        return add_person(authority_redis,
                          person_attributes,
                          person_metaphones_keys)
    # Try extracting the union of person_metaphone,dob_metaphones, and
    # dod_metaphones
    found_persons = []
    if len(person_metaphones_keys) > 0 and\
       len(dob_keys) > 0 and\
       len(dod_keys) > 0:
        found_persons = [get_person(redis_key,authority_redis) for redis_key in list(person_keys.intersection(dob_keys,dod_keys))]
        
    # Matches on person_metaphones_keys and dob_keys (for creators that
    # are still living)
    elif len(person_metaphones_keys) > 0 and\
         len(dob_keys) > 0:
        found_persons = [get_person(redis_key, authority_redis) for redis_key in list(person_keys.intersection(dob_keys))]
    if len(found_persons) == 1:
        return found_persons[0]
    elif len(found_persons) > 0:
        return found_persons
    # Assumes that person does not exist, add to datastore
    else:
        return add_person(authority_redis,
                          person_attributes,
                          person_metaphones_keys)

def person_search(raw_name,
		  authority_redis=AUTHORITY_REDIS,
		  join_operation='AND'):
    """
    Function takes a user supplied name and searches person metaphones
    and returns any matching bibframe:Authority:Person's CreativeWork keys.

    :param raw_name: Name of person
    :param join_operation: "AND","OR" stings, default is an "AND" search
    """
    all_work_keys,person_keys = [],[]
    person_metaphones = process_name(raw_name)
    metaphone_keys = ["person-metaphones:{0}".format(x) for x in person_metaphones]
    if join_operation == "OR":
        person_keys = authority_redis.sunion(metaphone_keys)
    else: # Default is an AND search
        person_keys = authority_redis.sinter(metaphone_keys)
    if len(person_keys) > 0:
        all_work_keys = authority_redis.sunion(["{0}:rda:isCreatorPersonOf".format(x) for x in person_keys])
    return all_work_keys
    
     
def process_name(raw_name):
    person_metaphones = []
    raw_names = raw_name.split(" ")
    for name in raw_names:
        first_phonetic,second_phonetic = metaphone.dm(name.decode('utf8',
                                                                  'ignore'))
        person_metaphones.append(first_phonetic)
    return person_metaphones
