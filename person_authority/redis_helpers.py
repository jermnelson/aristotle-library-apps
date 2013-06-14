"""
 :mod:`redis_helpers` Person Authority Helper Utilities
"""
__author__ = "Jeremy Nelson"
from bibframe.models import Person

import aristotle.lib.metaphone as metaphone
from bibframe.redis_helpers import get_brief
from title_search.redis_helpers import STOPWORDS
from aristotle.settings import REDIS_DATASTORE

def add_person(person_attributes,
               person_metaphones_keys,
               redis_datastore):
    """Function adds a BIBFRAME Person to RLSP 

    Function creates a new Person object using Redis Authority instance.

    Arguments:
    person_attributes -- Dictionary of attributes associated with the Person
    person_metaphones_keys -- Metaphones for Person's name
    redis_datastore -- Redis datastore, defaults to None
    """
    new_person = Person(redis_datastore=redis_datastore)
    for key, value in person_attributes.iteritems():
        setattr(new_person, key, value)
    new_person.save()
    for metaphone in person_metaphones_keys:
        redis_datastore.sadd(metaphone,new_person.redis_key)
    if hasattr(new_person, 'schema:dateOfBirth'):
        dob_key = 'person-dob:{0}'.format(
                      person_attributes.get('schema:dateOfBirth'))
        redis_datastore.sadd(dob_key,
                             new_person.redis_key)
    if hasattr(new_person, 'schema:dateOfDeath'):
        dod_key = "person-dod:{0}".format(
                      person_attributes.get('schema:dateOfDeath'))
        redis_datastore.sadd(dod_key, new_person.redis_key)
    return new_person


def get_person(person_redis_key,
               redis_datastore=None):
    """Function gets a bibframe.models.Person

    Function instantiates a bibframe.model.Person using a Person's Redis Key 
    Arguments:
    person_redis_key -- Person Redis Key
    redis_datastore -- Redis datastore, defaults to None
    """
    if redis_datastore is not None:
        existing_person = Person(redis_datastore=redis_datastore,
                                 redis_key=person_redis_key)
    else:
        msg = "get_person requires a Redis datastore"
        raise PersonAuthorityError(msg)
    return existing_person
                             

def get_or_generate_person(person_attributes, 
                           redis_datastore):
    """
    Method either returns a new Person or an existing Person based
    on a similarity metric.

    :param person_attributes: Person attributes in a dict
    :param redis_datastore: BIBFRAME Redis datastore
    """
    person_metaphones, person_metaphones_keys, person_keys = [],[],[]
    dob_keys,dod_keys = [],[]
    if person_attributes.has_key("rda:preferredNameForThePerson"):
        raw_name = person_attributes.get("rda:preferredNameForThePerson")
        person_metaphones = process_name(raw_name)
        person_metaphones_keys = ["person-metaphones:{0}".format(x) for x in person_metaphones]
        person_keys = redis_datastore.sinter(person_metaphones_keys)
    if person_attributes.has_key("schema:dateOfBirth"):
        raw_dob = person_attributes.get('schema:dateOfBirth')
        dob_keys = redis_datastore.smembers('person-dob:{0}'.format(raw_dob))
    if person_attributes.has_key("schema:dateOfDeath"):
        raw_dod = person_attributes.get('schema:dateOfDeath')
        dod_keys = redis_datastore.smembers('person-dod:{0}'.format(raw_dod))
    # No match on names, assume Person is not in the datastore and add to datastore
    if len(person_keys) <= 0:
        return add_person(person_attributes,
                          person_metaphones_keys,
                          redis_datastore)
    # Try extracting the union of person_metaphone,dob_metaphones, and
    # dod_metaphones
    found_persons = []
    if len(person_metaphones_keys) > 0 and\
       len(dob_keys) > 0 and\
       len(dod_keys) > 0:
        found_persons = [get_person(redis_key,redis_datastore) for redis_key in list(person_keys.intersection(dob_keys,dod_keys))]
        
    # Matches on person_metaphones_keys and dob_keys (for creators that
    # are still living)
    elif len(person_metaphones_keys) > 0 and\
         len(dob_keys) > 0:
        found_persons = [get_person(redis_key, redis_datastore) for redis_key in list(person_keys.intersection(dob_keys))]
    if len(found_persons) == 1:
        return found_persons[0]
    elif len(found_persons) > 0:
        return found_persons
    # Assumes that person does not exist, add to datastore
    else:
        return add_person(person_attributes,
                          person_metaphones_keys,
                          redis_datastore)

def person_search(raw_name,
		  redis_datastore=REDIS_DATASTORE,
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
        person_keys = redis_datastore.sunion(metaphone_keys)
    else: # Default is an AND search
        person_keys = redis_datastore.sinter(metaphone_keys)
    if len(person_keys) > 0:
        all_work_keys = redis_datastore.sunion(["{0}:rda:isCreatorPersonOf".format(x) for x in person_keys])
    return all_work_keys
    
     
def process_name(raw_name):
    person_metaphones = []
    raw_name = ' '.join(raw_name.split(","))
    raw_names = raw_name.split(" ")
    for name in raw_names:
        try:
            name = name.decode('utf-8', 'ignore')
        except UnicodeEncodeError, e:
            pass
        first_phonetic,second_phonetic = metaphone.dm(name)
        person_metaphones.append(first_phonetic)
    return person_metaphones
