"""
 :mod:`redis_helpers` Call Number Helper Utilities
"""
__author__ = "Jeremy Nelson"
import pymarc,redis,re
import logging,sys
from app_settings import APP,SEED_RECORD_ID
import aristotle.settings as settings
authority_redis = settings.AUTHORITY_REDIS
redis_server = settings.INSTANCE_REDIS
creative_work_redis = settings.CREATIVE_WORK_REDIS

english_alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 
                    'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 
                    'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 
                    'Y', 'Z']

lccn_first_cutter_re = re.compile(r"^(\D+)(\d+)")
#lc_regex = re.compile(r"^(?P<leading>[A-Z]{1,3})(?P<number>\d{1,4}.?\w{0,1}\d*)\s*(?P<decimal>[.|\w]*\d*)\s*(?P<cutter1alpha>\w*)\s*(?P<last>\d*)")
lc_regex = re.compile(r"^(?P<leading>[A-Z]{1,3})(?P<number>\d{1,4}.?\d{0,1}\d*)\s*(?P<cutter1>[.|\w]*\d*)\s*(?P<cutter2>\w*)\s*(?P<last>\d*)")


def generate_call_number_app(instance,redis_server):
    """
    Helper function takes a MARCR Instance with call-numbers, creates supporting
    Redis datastructures to support the call number app

    :param instance: MARCR Instance
    :parm redis_server: Redis server
    """
    identifiers = getattr(instance,'rda:identifierForTheManifestation',{})
    if identifiers.has_key('lccn'):
        redis_server.hset('lccn-hash',
                          identifiers.get('lccn'),
                          instance.redis_key)
        normalized_call_number = lccn_normalize(identifiers.get('lccn'))
        redis_server.hset('lccn-normalized-hash',
                          normalized_call_number,
                          instance.redis_key)
        redis_server.zadd('lccn-sort-set',
                          0,
                          normalized_call_number)
        instance.attributes['rda:identifierForTheManifestation']['lccn-normalized'] = normalized_call_number
        instance.save()
    if identifiers.has_key('sudoc'):
        call_number = identifiers.get('sudoc')
        redis_server.hset('sudoc-hash',
                          call_number,
                          instance.redis_key)
        redis_server.zadd('sudoc-sort-set',
                          0,
                          call_number)
    if identifiers.has_key('local'):
        call_number = identifiers.get('local')
        redis_server.hset('local-hash',
                          call_number,
                          instance.redis_key)
        redis_server.zadd('local-sort-set',
                          0,
                          call_number)
        
        
        
    
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
             call_number_type='lccn'):
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
             call_number_type='lccn'):
    """
    Function takes a call_number, iterates through Redis datastore hash values
    for lccn, sudoc, and local, and if call_number is present returns the
    rank from the sorted set.

    :param call_number: Call Number String
    :param call_number_type: Type of call number (lccn, sudoc, or local)
    :rtype integer or None:
    """
    if redis_server.hexists("{0}-hash".format(call_number_type),
                            call_number):
        entity_key = redis_server.hget("{0}-hash".format(call_number_type),
                                       call_number)
        ident_key = "{0}:rda:identifierForTheManifestation".format(entity_key)
        entity_idents = redis_server.hgetall(ident_key)
        if entity_idents.has_key("{0}-normalized".format(call_number_type)):
            current_rank = redis_server.zrank('{0}-sort-set'.format(call_number_type),
                                              entity_idents["{0}-normalized".format(call_number_type)])
        else:
            current_rank = redis_server.zrank('{0}-sort-set'.format(call_number_type),
                                              entity_idents[call_number_type])
        return current_rank
            

def get_slice(start,stop,
              call_number_type='lccn'):
    """
    Function gets a list of entities saved as Redis records

    :param start: Beginning of slice of sorted call number
    :param stop: End of slice of sorted call numbers
    :param call_number_type: Type of call number (lccn, sudoc, or local), defaults
                             to lccn.
    :rtype: List of entities saved as Redis records
    """
    entities = []
    record_slice = redis_server.zrange('{0}-sort-set'.format(call_number_type),
                                       start,
                                       stop)
    for number in record_slice:
        if call_number_type == 'lccn':
            entity_key = redis_server.hget('lccn-normalized-hash',number)
        else:
            entity_key = redis_server.hget('{0}-hash'.format(call_number_type),
                                           number)
        call_number = redis_server.hget('{0}:rda:identifierForTheManifestation'.format(entity_key),
                                        call_number_type)
        record = get_record(call_number=call_number)
        entities.append(record)
    return entities

def get_record(**kwargs):
    call_number = kwargs.get('call_number')
    record_info = {'call_number':call_number}
    for hash_base in ['lccn','sudoc','local']:
        hash_name = '{0}-hash'.format(hash_base)
        if redis_server.hexists(hash_name,call_number):
            record_info['type_of'] = hash_base
            instance_key = redis_server.hget(hash_name,call_number)
            record_info['bib_number'] = redis_server.hget('{0}:rda:identifierForTheManifestation'.format(instance_key),
                                                          'ils-bib-number')
            work_key = redis_server.hget(instance_key,'bibframe:CreativeWork')
            record_info['title'] = creative_work_redis.hget("{0}:rda:Title".format(work_key),
                                                  'rda:preferredTitleForTheWork')
            creator_keys = creative_work_redis.smembers("{0}:rda:creator".format(work_key))
            if len(creator_keys) > 0:
                creator_keys = list(creator_keys)
                creator = authority_redis.hget(creator_keys[0],
                                               "rda:preferredNameForThePerson")
                if len(creator_keys) > 1:
                    creator += " et.al."
                record_info['authors'] = unicode(creator,encoding="utf-8",errors='ignore')
            return record_info
    return None
    

def lccn_normalize(raw_callnumber):
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
    normalized_call_number = lccn_normalize(call_number)
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
    
    
    
