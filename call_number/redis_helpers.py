"""
 :mod:`redis_helpers` Call Number Helper Utilities
"""
import pymarc,redis,re
import logging,sys
try:
    import aristotle.settings as settings
    REDIS_HOST = settings.REDIS_ACCESS_HOST
    REDIS_PORT = settings.REDIS_ACCESS_PORT
    CALL_NUMBER_DB = settings.CALL_NUMBER_DB
    volatile_redis = redis.StrictRedis(host=settings.REDIS_PRODUCTIVITY_HOST,
                                       port=settings.REDIS_PRODUCTIVITY_PORT,
                                       db=CALL_NUMBER_DB)

except ImportError:
    # Setup for local development
#    REDIS_HOST = '172.25.1.108'
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    CALL_NUMBER_DB = 4
    volatile_redis = None
    

redis_server = redis.StrictRedis(host=REDIS_HOST,
                                 port=REDIS_PORT,
                                 db=CALL_NUMBER_DB)


english_alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 
                    'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 
                    'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 
                    'Y', 'Z']

lccn_first_cutter_re = re.compile(r"^(\D+)(\d+)")
lc_regex = re.compile(r"^(?P<leading>[A-Z]{1,3})(?P<number>\d{1,4}.?\w{0,1}\d*)\s*(?P<decimal>[.|\w]*\d*)\s*(?P<cutter1alpha>\w*)\s*(?P<last>\d*)")

def generate_search_set(call_number):
    if volatile_redis is None:
        return None
    redis_server = volatile_redis
    sections = call_number.split(".")
    first_cutter = sections[0].strip()
    for i in range(0,len(first_cutter)):
        redis_server.zadd('call-number-sorted-search-set',0,first_cutter[0:i])
    redis_server.zadd('call-number-sorted-search-set',0,first_cutter)
    redis_server.zadd('call-number-sorted-search-set',0,'%s*' % call_number)   

def get_callnumber(record,
                   marc_fields=['086',
                                '090',
                                '099',
                                '050']):
    """
    Function iterates through the marc_fields list and returns 
    the first field that has a value. List order matters in 
    this function!

    :param record: MARC Record
    :param marc_fields: List of MARC Fields that contain call numbers
    :rtype str: First matched string
    """
    for field_tag in marc_fields:
        if record[field_tag] is not None:
            return record[field_tag].value()

def get_all(call_number,slice_size=10):
    """
    Function returns a list of call numbers with the param centered between
    the slice_size

    :param call_number: Call Number as stored in call-number-sort-set
    :param slice_size: Slice size, default is 10
    :rtype list: List of call numbers
    """
    current_rank = redis_server.zrank('call-number-sort-set',call_number)
    return redis_server.zrange('call-number-sort-set',
                               current_rank-slice_size,
                               current_rank+slice_size)


def get_previous(call_number):
    """
    Function returns a list of two records that preceed the current
    param call_number using the get_slice method.

    :param call_number: Call Number String
    :rtype list: List of two records 
    """
    current_rank = redis_server.zrank('call-number-sort-set',call_number)
    return get_slice(current_rank-2,current_rank-1)

def get_next(call_number):
    """
    Function returns a list of two records that follow the current
    param call_number using the get_slice method.

    :param call_number: Call Number String
    :rtype list: List of two records 
    """

    current_rank = redis_server.zrank('call-number-sort-set',call_number)
    return get_slice(current_rank+1,current_rank+2)


def get_redis_info():
    redis_info = {'dbsize':redis_server.dbsize(),
                  'info':redis_server.info(),
                  'call_number_size':len(redis_server.hkeys('call-number-hash'))}
    return redis_info

def get_slice(start,stop):
    """
    Function gets a list of entities saved as Redis records

    :param start: Beginning of 
    :param stop: End of slice of sorted call numbers
    :rtype: List of entities saved as Redis records
    """
    entities = []
    record_slice = redis_server.zrange('call-number-sort-set',start,stop)
    for number in record_slice:
        entities.append(get_record(number))
    return entities

def get_record(call_number):
    record_key = redis_server.hget('call-number-hash',call_number)
    return redis_server.hgetall(record_key)

def quick_set_callnumber(identifiers_key,
                         call_number_type,
                         call_number,
                         redis_key):
    redis_server.hset(identifiers_key,
                      call_number_type,
                      call_number)
    redis_server.hset('%s-hash' % call_number_type,call_number,redis_key)
    redis_server.zadd('%s-sort-set' % call_number_type,0,call_number)

def get_set_callnumbers(redis_key,
                        marc_record):
    """
    Sets sudoc, lc, and local call numbers from the MARC record values

    :param redis_key: Key to RDA Core entity 
    :param marc_record: MARC21 record
    """
    identifiers_key = '%s:identifiers' % redis_key
    sudoc_field = marc_record['086']
    if sudoc_field is not None:
        call_number = sudoc_field.value()
        quick_set_callnumber(identifiers_key,
                             "sudoc",
                             call_number,
                             redis_key)
    lccn_field = marc_record['050']
    if lccn_field is not None:
        call_number = lccn_field.value()
        redis_server.hset(identifiers_key,
                          'lccn',
                          call_number)
        redis_server.hset('lccn-hash',call_number,redis_key)
        redis_server.zadd('lccn-sort-set',0,call_number)
    local_090 = marc_record['090']
    if local_090 is not None:
        call_number = local_090.value()
        quick_set_callnumber(identifiers_key,
                             "local",
                             call_number,
                             redis_key)
    local_099 = marc_record['099']
    if local_099 is not None:
        call_number = local_099.value()
        quick_set_callnumber(identifiers_key,
                             "local",
                             call_number,
                             redis_key)
        
    


def ingest_record(marc_record):
    if volatile_redis is None:
        print("Volatile Redis not available")
        return None
    redis_server = volatile_redis
    bib_number = marc_record['907']['a'][1:-1]
    call_number = get_callnumber(marc_record)
    if call_number is None:
        return None
    redis_id = redis_server.incr("global:frbr_rda")
    redis_key = ":%s" % redis_id
    redis_server.hset(redis_key,"rdaTitleOfWork",marc_record.title())
    redis_server.hset(redis_key,
                      "rdaRelationships:author",
                      marc_record.author())
    identifiers_key = '%s:identifiers' % redis_key
    redis_server.hset(identifiers_key,
                      'bibliographic-number',
                      bib_number)
    get_set_callnumbers(redis_key,
                        marc_record)
    redis_server.hset(redis_key,"rdaIdentifierForTheExpression",
                      '%s:identifiers' % redis_key)
    isbn = marc_record.isbn()
    if isbn is not None:
        redis_server.hset('%s:identifiers' % redis_key,
                          "isbn",
                          isbn)
    # Create search set
    generate_search_set(call_number)
    redis_server.hset('bib-number-hash',bib_number,redis_key)
    redis_server.hset('call-number-hash',call_number,redis_key)
    redis_server.zadd('call-number-sort-set',0,call_number) 


def ingest_records(marc_file_location):
    if volatile_redis is None:
        return None
    marc_reader = pymarc.MARCReader(open(marc_file_location,"rb"))
    for record in marc_reader:
        ingest_record(record)
    

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
    callnumber_regex = lc_regex.search(raw_callnumber)
    output = None
    if callnumber_regex is not None:
        callnumber_result = callnumber_regex.groupdict()
        leading = callnumber_result.get('leading')
    return output
        
