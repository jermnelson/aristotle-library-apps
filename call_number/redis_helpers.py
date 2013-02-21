"""
 :mod:`redis_helpers` Call Number Helper Utilities
"""
__author__ = "Jeremy Nelson"
import pymarc,redis,re
import logging,sys
from app_settings import APP,SEED_RECORD_ID
import aristotle.settings as settings
annotation_server = settings.ANNOTATION_REDIS
authority_redis = settings.AUTHORITY_REDIS
redis_server = settings.INSTANCE_REDIS
creative_work_server = settings.CREATIVE_WORK_REDIS

english_alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 
                    'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 
                    'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 
                    'Y', 'Z']

lccn_first_cutter_re = re.compile(r"^(\D+)(\d+)")
#lc_regex = re.compile(r"^(?P<leading>[A-Z]{1,3})(?P<number>\d{1,4}.?\w{0,1}\d*)\s*(?P<decimal>[.|\w]*\d*)\s*(?P<cutter1alpha>\w*)\s*(?P<last>\d*)")
lc_regex = re.compile(r"^(?P<leading>[A-Z]{1,3})(?P<number>\d{1,4}.?\d{0,1}\d*)\s*(?P<cutter1>[.|\w]*\d*)\s*(?P<cutter2>\w*)\s*(?P<last>\d*)")


def generate_call_number_app(instance,
                             instance_server,
                             annotation_server=settings.ANNOTATION_REDIS):
    """
    Helper function takes a BIBFRAME Instance, extracts any call-numbers from the
    any associated Library Holdings, and creates supporting
    Redis datastructures to support the call number app

    :param instance: BIBFRAME Instance
    :param instance_server: Redis server
    :param annotation_server: 
    """
    has_annotations_key = "{0}:hasAnnotation".format(instance.redis_key)
    annotations = instance_server.smembers(has_annotations_key)
    for annotation_key in annotations:
        if annotation_key.startswith('bibframe:Holding'):
            if annotation_server.hexists(annotation_key,'callno-lcc'):
                callno_lcc = annotation_server.hget(annotation_key,
                                                    'callno-lcc')
                annotation_server.hset('lcc-hash',
                                       callno_lcc,
                                       annotation_key)
                normalized_call_number = lccn_normalize(callno_lcc)
                annotation_server.hset('lcc-normalized-hash',
                                       normalized_call_number,
                                       annotation_key)
                annotation_server.zadd('lcc-sort-set',
                                       0,
                                       normalized_call_number)
            if annotation_server.hexists(annotation_key,'callno-govdoc'):
                callno_govdoc = annotation_server.hget(annotation_key,
                                                       'callno-govdoc')
                annotation_server.hset('govdoc-hash',
                                       callno_govdoc,
                                       annotation_key)
                annotation_server.zadd('govdoc-sort-set',
                                  0,
                                  callno_govdoc)
            if annotation_server.hexists(annotation_key,'callno-local'):
                 callno_local = annotation_server.hget(annotation_key,
                                                       'callno-local')
                 annotation_server.hset('local-hash',
                                        callno_local,
                                        annotation_key)
                 annotation_server.zadd('local-sort-set',
                                        0,
                                        callno_local)
    for name in ['isbn','issn','lccn']:
        if hasattr(instance,name) and getattr(instance,name) is not None:
            for value in list(getattr(instance,name)): 
                instance_server.hset('{0}-hash'.format(name), 
                                     value,
                                     instance.redis_key)
                instance_server.zadd('{0}-sort-set'.format(name),
                                     0,
                                     value)

        
        
    
def get_all(call_number,slice_size=10):
    """
    Function returns a list of call numbers with the param centered between
    the slice_size

    :param call_number: Call Number as stored in call-number-sort-set
    :param slice_size: Slice size, default is 10
    :rtype list: List of call numbers
    """
    lccn_rank = redis_server.zrank('lccn-sort-set',call_number)
    if lccn_rank is not None:
        return redis_server.zrange('lccn-sort-set',
                                   lccn_rank-slice_size,
                                   lccn_rank+slice_size)
    sudoc_rank = redis_server.zrank('sudoc-sort-set',call_number)
    if sudoc_rank is not None:
        return redis_server.zrange('sudoc-sort-set',
                                   sudoc_rank-slice_size,
                                   sudo_rank+slice_size)
    local_rank = redis_server.zrank('local-sort-set',call_number)
    if local_rank is not None:
        return redis_server.zrange('local-sort-set',
                                   local_rank-slice_size,
                                   local_rank+slice_size)
        


def get_previous(call_number,
                 call_number_type='lccn'):
    """
    Function returns a list of two records that preceed the current
    param call_number using the get_slice method.

    :param call_number: Call Number String
    :param call_number_type: Type of call number (lccn, sudoc, or local)
    :rtype list: List of two records 
    """
    current_rank = get_rank(call_number,
                            call_number_type=call_number_type)
    if current_rank is None:
        return None
    return get_slice(current_rank-2,
                     current_rank-1,
                     call_number_type)

def get_next(call_number,
             call_number_type='lcc'):
    """
    Function returns a list of two records that follow the current
    param call_number using the get_slice method.

    :param call_number: Call Number String
    :param call_number_type: Type of call number (lccn, sudoc, or local)
    :rtype list: List of two records 
    """
    current_rank = get_rank(call_number,
                            call_number_type=call_number_type)
    if current_rank is None:
        return None
    return get_slice(current_rank+1,
                     current_rank+2,
                     call_number_type)

def get_rank(call_number,
             call_number_type='lcc'):
    """
    Function takes a call_number, iterates through Redis datastore hash values
    for lccn, sudoc, and local, and if call_number is present returns the
    rank from the sorted set.

    :param call_number: Call Number String
    :param call_number_type: Type of call number (lcc, sudoc, local, )
    :rtype integer or None:
    """
    current_rank = -1
    hash_key = "{0}-hash".format(call_number_type)
    sort_set_key = '{0}-sort-set'.format(call_number_type)
    if annotation_server.exists(hash_key):
        # Currently we are only creating normalized values for LCC call number
        if call_number_type == 'lcc': 
            normalized_call_number = lcc_normalize(call_number)
            current_rank = annotation_server.zrank(sort_set_key,
                                                   normalized_call_number)
        else:
            current_rank = annotation_server.zrank(sort_set_key,
                                                   call_number)

    elif redis_server.exists(hash_key): 
        current_rank = redis_server.zrank(sort_set_key,
                                          call_number)
    return current_rank
            

def get_slice(start,stop,
              call_number_type='lcc'):
    """
    Function gets a list of entities saved as Redis records

    :param start: Beginning of slice of sorted call number
    :param stop: End of slice of sorted call numbers
    :param call_number_type: Type of call number (lccn, sudoc, or local), defaults
                             to lcc.
    :rtype: List of entities saved as Redis records
    """
    entities = []
    hash_key = '{0}-hash'.format(call_number_type)
    sort_set_key = '{0}-sort-set'.format(call_number_type)
    if annotation_server.exists(sort_set_key):
        record_slice = annotation_server.zrange(sort_set_key,
                                                start,
                                                stop)
    elif redis_server.exists(sort_set_key):
        record_slice = redis_server.zrange(sort_set_key,
                                           start,
                                           stop)
    else:
        raise ValueError("get_slice error, {0} not in Annotation or Instance Redis instances".format(sort_set_key))
 
    for number in record_slice:
        if call_number_type == 'lcc':
            annotation_key = annotation_server.hget('lcc-normalized-hash',number)
            entity_key = annotation_server.hget(annotation_key,'annotates')
            call_number = annotation_server.hget(annotation_key,'callno-lcc')
        elif annotation_server.exists(hash_key):
            annotation_key = annotation_server.hget(hash_key,number)
            entity_key = annotation_server.hget(annotation_key,'annotates')
            call_number = annotation_server.hget(annotation_key,"callno-{0}".format(call_number_type))
        elif redis_server.exists(hash_key):
            entity_key = redis_server.hget(hash_key, number)
            call_number = redis_server.hget(entity_key,call_number_type)
        record = get_record(call_number=call_number,
                            instance_key=entity_key)
        entities.append(record)
    return entities

def get_record(**kwargs):
    record_info = {'call_number':kwargs.get('call_number')}
    if kwargs.has_key('work_key'):
        record_info['work_key'] = kwargs.get('work_key')
    elif kwargs.has_key('instance_key'):
        instance_key = kwargs.get('instance_key')
        record_info['work_key'] = redis_server.hget(instance_key, 'instanceOf')
    else:
        # Try searching for call_number in Instance datastores
        for name in ['isbn','issn']:
            if redis_server.hexists("{0}-hash".format(name),
                                    record_info['call_number']):
                instance_key = redis_server.hget("{0}-hash".format(name),
                                                 record_info['call_number'])
                record_info['work_key'] = redis_server.hget(instance_key, 'instanceOf')
                record_info['type_of'] = name
                break
        # Trys searching for call_number in Annotation datastore
        if 'work_key' not in record_info:
            for name in ['lcc','govdoc','local']:
                hash_key = "{0}-hash".format(name)
                if annotation_server.hexists(hash_key,
                                             record_info['call_number']):
                    record_info['type_of'] = name
                    holding_key = annotation_server.hget(hash_key,
                                                         record_info['call_number'])
                    instance_key = annotation_server.hget(holding_key,
                                                          "annotates")
                    
                    record_info['work_key'] = redis_server.hget(instance_key, 
                                                                'instanceOf')
                    break
        
    record_info['title'] = creative_work_server.hget("{0}:title".format(record_info['work_key']),
                                                     'rda:preferredTitleForTheWork')
    record_info['title'] = unicode(record_info['title'], encoding="utf-8", errors="ignore")
    if creative_work_server.exists('{0}:rda:isCreatedBy'.format(record_info['work_key'])):
        creator_keys = list(creative_work_server.smembers('{0}:rda:isCreatedBy'.format(record_info['work_key'])))
    elif creative_work_server.hexists(record_info['work_key'],'rda:isCreatedBy'):
        creator_keys = [creative_work_server.hget(record_info['work_key'],
                                                  'rda:isCreatedBy'),]
    else:
        creator_keys = []
    if len(creator_keys) > 0:
        creator = authority_redis.hget(creator_keys[0],"rda:preferredNameForThePerson")
        if len(creator_keys) > 1:
            creator += ' et.al.'
        record_info['authors'] = unicode(creator,encoding="utf-8",errors='ignore')
    return record_info

    


def old_get_record(**kwargs):
    call_number = kwargs.get('call_number')
    record_info = {'call_number':call_number}
    for hash_base in ['lcc','govdoc','local']:
        hash_name = '{0}-hash'.format(hash_base)
        
        if annotation_server.hexists(hash_name,call_number):
            record_info['type_of'] = hash_base
            holding_key = annotation_server.hget(hash_name,call_number)
            instance_key = annotation_server.hget(holding_key,'annotates')
            record_info['bib_number'] = redis_server.hget('{0}:rda:identifierForTheManifestation'.format(instance_key),
                                                          'ils-bib-number')
            work_key = redis_server.hget(instance_key,'instanceOf')
            record_info['title'] = creative_work_redis.hget("{0}:title".format(work_key),
                                                  'rda:preferredTitleForTheWork')
            creator_keys = creative_work_redis.smembers("{0}:rda:isCreatedBy".format(work_key))
            if len(creator_keys) > 0:
                creator_keys = list(creator_keys)
                creator = authority_redis.hget(creator_keys[0],
                                               "rda:preferredNameForThePerson")
                if len(creator_keys) > 1:
                    creator += " et.al."
                record_info['authors'] = unicode(creator,encoding="utf-8",errors='ignore')
            return record_info
    return None
    

def lcc_normalize(raw_callnumber):
    """
    Function based on Bill Dueber algorithm at
    <http://code.google.com/p/library-callnumber-lc/wiki/Home>
    """
    callnumber_regex = lc_regex.search(raw_callnumber)
    output = None
    if callnumber_regex is not None:
        callnumber_result = callnumber_regex.groupdict()
        output = '%s ' % callnumber_result.get('leading')
        number = callnumber_result.get('number')
        number_lst = number.split(".")
        output += '{:>04}'.format(number_lst[0])
        if len(number_lst) == 2:
            output += '{:<02}'.format(number_lst[1])
        cutter1 = callnumber_result.get('cutter1')
        if len(cutter1) > 0:
            cutter1 = cutter1.replace('.','')
            output += '{:<04}'.format(cutter1)
        cutter2 = callnumber_result.get('cutter2')
        if len(cutter2) > 0:
            cutter2 = cutter2.replace('.','')
            output +=  '{:<04}'.format(cutter2)
    return output
        
def lccn_set(identifiers_key,
             call_number,
             redis_server,
             redis_key):
    """
    Sets hash and sorted set for normalized and raw call numbers for
    LCCN call numbers
    
    :param identifiers_key: Key to the RDA Records rdaIdentifiersForTheExpression
    :param call_number: LCCN Call number
    :param redis_server: Redis Server
    :param redis_key: Redis key
    """
    redis_server.hset(identifiers_key,
                      'lccn',
                      call_number)
    normalized_call_number = lcc_normalize(call_number)
    redis_server.hset(identifiers_key,
                      'lccn-normalized',
                      normalized_call_number)
    redis_server.hset('lccn-hash',call_number,redis_key)
    redis_server.hset('lccn-normalized-hash',
                      normalized_call_number,
                      redis_key)
    redis_server.zadd('lccn-sort-set',
                      0,
                      normalized_call_number)
    
    
    
