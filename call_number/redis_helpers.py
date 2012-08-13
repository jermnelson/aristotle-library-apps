"""
 :mod:`redis_helpers` Call Number Helper Utilities
"""
import pymarc,redis,re
import logging,sys
from app_settings import APP,SEED_RECORD_ID,REDIS_SERVER

redis_server = REDIS_SERVER

english_alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 
                    'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 
                    'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 
                    'Y', 'Z']

lccn_first_cutter_re = re.compile(r"^(\D+)(\d+)")
#lc_regex = re.compile(r"^(?P<leading>[A-Z]{1,3})(?P<number>\d{1,4}.?\w{0,1}\d*)\s*(?P<decimal>[.|\w]*\d*)\s*(?P<cutter1alpha>\w*)\s*(?P<last>\d*)")
lc_regex = re.compile(r"^(?P<leading>[A-Z]{1,3})(?P<number>\d{1,4}.?\d{0,1}\d*)\s*(?P<cutter1>[.|\w]*\d*)\s*(?P<cutter2>\w*)\s*(?P<last>\d*)")
   
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
    print("{0}-hash {1}".format(call_number_type,call_number))
    if redis_server.hexists("{0}-hash".format(call_number_type),
                            call_number):
        entity_key = redis_server.hget("{0}-hash".format(call_number_type),
                                       call_number)
        entity_idents = redis_server.hgetall("{0}:identifiers".format(entity_key))
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
        call_number = redis_server.hget('{0}:identifiers'.format(entity_key),
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
            record_key = redis_server.hget(hash_name,call_number)
            manifestation_key = redis_server.hget(record_key,
                                                  'rdaManifestationOfExpression')
            record_info['bib_number'] = redis_server.hget(manifestation_key,
                                                          'legacy-bib-number')
            title_list = list(redis_server.smembers(redis_server.hget(manifestation_key,
                                                                 'rdaTitle')))
            title_list.reverse()
            record_info['rdaTitle'] = u''.join([x.decode('utf-8','ignore') for x in title_list])
            work_key = redis_server.hget(manifestation_key,
                                         'rdaWorkManifested')
            if redis_server.hexists(work_key,
                                    'rdaCreator'):
                creator_key = redis_server.hget(work_key,
                                                'rdaCreator')
                creator = redis_server.hget(creator_key,
                                            'rdaPreferredNameForThePerson')
##                try:
##                    print("Creator is {0}".format(creator.decode('utf-8','xmlcharrefreplace')))
##                except:
##                    print("ERROR trying to extract creator")
##                    print("{0} {1}".format(creator,sys.exc_info()[0]))
                record_info['author'] = creator.decode('utf-8','ignore')
            return record_info
    
    
def quick_set_callnumber(identifiers_key,
                         call_number_type,
                         call_number,
                         redis_server,
                         redis_key):
    redis_server.hset(identifiers_key,
                      call_number_type,
                      call_number)
    redis_server.hset('%s-hash' % call_number_type,call_number,redis_key)
    redis_server.zadd('%s-sort-set' % call_number_type,0,call_number)



def get_set_callnumbers(marc_record,
                        redis_server,
                        redis_key):
    """
    Sets sudoc, lc, and local call numbers from the MARC record values
 
    :param marc_record: MARC21 record
    :param redis_server: Redis Server
    :param redis_key: Key to RDA Core entity
    """
    identifiers_key = '%s:identifiers' % redis_key
    if not redis_server.hexists(redis_key,'identifiers'):
        redis_server.hset(redis_key,'identifiers',identifiers_key)
    sudoc_field = marc_record['086']
    if sudoc_field is not None:
        call_number = sudoc_field.value()
        quick_set_callnumber(identifiers_key,
                             "sudoc",
                             call_number,
                             redis_server,
                             redis_key)
    lccn_field = marc_record['050']
    if lccn_field is not None:
        call_number = lccn_field.value()
        lccn_set(identifiers_key,
                 call_number,
                 redis_server,
                 redis_key)
        
    local_090 = marc_record['090']
    if local_090 is not None:
        call_number = local_090.value()
        if not redis_server.hget(identifiers_key,'lccn'):
            lccn_set(identifiers_key,
                     call_number,
                     redis_server,
                     redis_key)
        else:
            quick_set_callnumber(identifiers_key,
                                 "local",
                                 call_number,
                                 redis_server,
                                 redis_key)
    local_099 = marc_record['099']
    if local_099 is not None:
        call_number = local_099.value()
        quick_set_callnumber(identifiers_key,
                             "local",
                             call_number,
                             redis_server,
                             redis_key)
        
    
def ingest_call_numbers(marc_record,redis_server,entity_key):
    """
    `ingest_call_numbers` function takes a MARC record and
    a RDACore FRBR Redis Expression or Manifestation key, ingests the
    record and depending on the call number type (currently using
    three types of call numbers; LCCN, SuDoc, and local)
    associates the call number to the entity key in a
    hash and then adds the call number to a sorted set, with
    the weight score using a custom sort algorithm depending
    on the call number type.

    :param marc_record: MARC Record
    :param redis_server: Redis Server
    :param entity_key: Redis FRBR RDACore Entity key
    """
    get_set_callnumbers(marc_record,redis_server,entity_key)
    

def search(query):
    set_rank = redis_server.zrank('call-number-sorted-search-set',query)
    output = {'result':[]}
    for row in redis_server.zrange('call-number-sorted-search-set',set_rank,-1):
        if row[-1] == "*":
            call_number = row[:-1]
            record = get_record(call_number)
            output['result'].append(call_number)
            output['record'] = record
            output['discovery_url'] = '%s%s' % (settings.DISCOVERY_RECORD_URL,
                                                record['bib_number'])
            return output
        else:
            output['result'].append(row)
    return output


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
    
    
    
