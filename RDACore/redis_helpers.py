"""
 :mod:`redis_helpers` RDA Core Helper Utilities
"""
import pymarc,redis,re
import logging,sys
from app_settings import APP,SEED_RECORD_ID
try:
    import aristotle.settings as settings
    REDIS_HOST = settings.REDIS_ACCESS_HOST
    REDIS_PORT = settings.REDIS_ACCESS_PORT
    TEST_DB = settings.REDIS_TEST
    volatile_redis = redis.StrictRedis(host=settings.REDIS_PRODUCTIVITY_HOST,
                                       port=settings.REDIS_PRODUCTIVITY_PORT)

except ImportError:
    # Setup for local development
    REDIS_HOST = '172.25.1.108'
##    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    TEST_DB = 3
    volatile_redis = None
    

# RDA Core should reside on primary DB of 0
redis_server = redis.StrictRedis(host=REDIS_HOST,
                                 port=REDIS_PORT)    

def create_manifestation(marc_record,manifestation_key):
    """
    Ingests a RDA Core Manifestation into Redis datastore

    :param marc_record: MARC Record
    :param manifestation_key: Redis key for the Manifestation
    """
    if volatile_redis is None:
        raise ValueError("Volatile Redis not available")
    redis_server = volatile_redis
    redis_server.hset(manifestation_key,
                      "titleProper",
                      marc_record.title())
    # Statement of Responsibility
    field245s = marc_record.get_fields('245')
    statement_str = ''
    for field in field245s:
        subfield_c = field.get_subfields('c')
        statement_str += "".join(subfield_c)
    if len(statement_str) > 0:
        redis_server.hset(manifestation_key,
                          "statementOfResponsibility",
                          statement_str)
    # Edition statement
    field250s = marc_record.get_fields('250')
    for field in field250s:
        edition_stmt_key = "{0}:editionStatement".format(manifestation_key)
        subfield_a = field.get_subfields('a')
        if len(subfield_a) > 0:
            edition_designation = redis_server.hget(edition_stmt_key,
                                                    "designationOfEdition")
            if edition_designation is None:
                edition_designation = "{0}:designations".format(edition_stmt_key)
            redis_server.sadd(edition_designation,
                              ''.join(subfield_a))
            redis_server.hset(edition_stmt_key,
                              "designationOfEdition",
                              edition_designation)
        subfield_b = field.get_subfields('b')
        if len(subfield_b) > 0:
            named_revision = redis_server.hget(edition_stmt_key,
                                               "designationOfNamedRevisionOfEdition")
            
            if named_revision is None:
                named_revision = "{0}:namedRevisions".format(edition_stmt_key)
            redis_server.sadd(named_revision,
                              ''.join(subfield_b))
            redis_server.hset(edition_stmt_key,
                              "designationOfNamedRevisionOfEdition",
                              named_revision)
    # Production Statement
    production_stmt_key = "{0}:productionStatement".format(manifestation_key)
    date_sort_key = redis_server.hget(production_stmt_key,
                                      "dateOfProduction")
    if date_sort_key is None:
        date_sort_key = "{0}:dates" % production_stmt_key
        redis_server.hset(production_stmt_key,
                          "dateOfProduction",
                          date_sort_key)
    field008 = marc_record['008']
    if field008 is not None:
        field_values = list(field008.value())
        date1,date2 = field_values[7:10],field_values[11:14]
        if len(date1.strip()) > 0:
            redis_server.zadd(date_sort_key,
                              int(date1),
                              date1)
        if len(date2.strip()) > 0:
            redis_server.zadd(date_sort_key,
                              int(date2),
                              date2)
    process_tag_list_as_set(marc_record,
                            date_sort_key,
                            redis_server,
                            [('260','c'),
                             ('542','j')],
                            is_sorted=True)
    # Publication Statement
    pub_stmt_key = "{0}:publicationStatement".format(manifestation_key)
    place_set_key = redis_server.hget(pub_stmt_key,
                                      "placeOfPublication")
    if place_set_key is None:
        place_set_key = "{0}:places".format(pub_stmt_key)
        redis_server.hget(pub_stmt_key,
                      "placeOfPublication",
                      place_set_key)
    process_tag_list_as_set(marc_record,
                            place_set_key,
                            redis_server,
                            [('260','a'),
                             ('542','k'),
                             ('542','p')])    
    pub_name_set_key = redis_server.hget(pub_stmt_key,
                                         "publisherName")
    if pub_name_set_key is None:
        pub_name_set_key = "{0}:publishers".format(pub_stmt_key)
        redis_server.hset(pub_stmt_key,
                          "publisherName",
                          pub_name_set_key)
    process_tag_list_as_set(marc_record,
                            pub_name_set_key,
                            redis_server,
                            [('260','b'),
                             ('542','k')])

        
            
def process_tag_list_as_set(marc_record,
                            redis_key,
                            redis_server,
                            tag_list,
                            is_sorted=False):
    """
    Helper function takes a MARC record, a RDA redis key for the set,
    and a listing of MARC Field tags and subfields, and adds each
    TAG-VALUE to the set or sorted set

    :param marc_record: MARC record
    :param redis_key: Redis key for the set or sorted set
    :param redis_server: Redis datastore instance
    :param tag_list: A listing of ('tag','subfield') tuples
    :param is_sorted: Boolean if sorted set, default is False
    """
    for tag in tag_list:
        all_fields = marc_record.get_fields(tag[0])
        for field in all_fields:
            subfields = field.get_subfields(tag[1])
            for subfield in subfields:
                if is_sorted is True:
                    redis_server.zadd(redis_key,
                                      subfield,
                                      subfield)
                else:
                    redis_server.sadd(redis_key,subfield)
    
            
            
                
                                  
    
    

def ingest_record(marc_record):
    if volatile_redis is None:
        print("Volatile Redis not available")
        return None
    redis_server = volatile_redis
    bib_number = marc_record['907']['a'][1:-1]
    redis_id = redis_server.incr("global:frbr_rda")
    redis_key = "rdaCore:%s" % redis_id
    manifestation_key = "%s:Manifestation:%s" % (redis_key,
                                                 redis_server.incr("global:%s:Manifestation" % redis_key))
    create_manifestation(marc_record,manifestation_key)
    
    
    redis_server.

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
#    generate_search_set(call_number)
    redis_server.hset('bib-number-hash',bib_number,redis_key)
    redis_server.hset('call-numbers-hash',call_number,redis_key)
    redis_server.zadd('call-number-sort-set',0,call_number) 


def ingest_records(marc_file_location):
    if volatile_redis is None:
        return None
    marc_reader = pymarc.MARCReader(open(marc_file_location,"rb"))
    for i,record in enumerate(marc_reader):
        if not i%1000:
            sys.stderr.write(".")
        if not i%10000:
            sys.stderr.write(str(i))
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
             redis_key):
    """
    Sets hash and sorted set for normalized and raw call numbers for
    LCCN call numbers
    
    :param identifiers_key: Key to the RDA Records rdaIdentifiersForTheExpression
    :param call_number: LCCN Call number
    :param redis_key: Redis key
    """
    redis_server.hset(identifiers_key,
                      'lccn',
                      call_number)
    normalized_call_number = lccn_normalize(call_number)
    redis_server.hset(identifiers_key,
                      'lccn-normalized',
                      normalized_call_number)
    redis_server.hset('lccn-hash',normalized_call_number,redis_key)
    redis_server.zadd('lccn-sort-set',
                      0,
                      normalized_call_number)
    
    
    
