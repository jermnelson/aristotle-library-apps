"""
 :mod:`frbr_redis` Module ingests MARC records into a FRBR-Redis datastore 
 controlled by the MARC Batch app. This Module initially ingests the RDA
 core elements from MARC into datastore.
"""
__author__ = 'Jeremy Nelson'
import pymarc,redis,logging,sys


try:
    import aristotle.settings as settings
    REDIS_HOST = settings.REDIS_ACCESS_HOST
    REDIS_PORT = settings.REDIS_ACCESS_PORT
    TEST_DB = settings.REDIS_TEST
    volatile_redis = redis.StrictRedis(host=settings.REDIS_PRODUCTIVITY_HOST,
                                       port=settings.REDIS_PRODUCTIVITY_PORT)
except:
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    REDIS_TEST_DB = 3

# RDA Core should reside on primary DB of 0
redis_server = redis.StrictRedis(host=REDIS_HOST,
                                 port=REDIS_PORT)    


class CreateRDACoreEntityFromMARC(object):
    """RDACoreEntity is the base class for ingesting MARC21 records into RDACore
    FRBR entities stored in Redis.

    This class is meant to be over-ridden by child classes for specific RDACore Entities.

    The general 


    """

    def __init__(self,**kwargs):
        self.marc_record = kwargs.get('record')
        self.redis_server = kwargs.get('redis_server')
        self.root_redis_key = kwargs.get('root_redis_key')
        entity_name = kwargs.get('entity')
        redis_incr_value = self.redis_server.incr("global:{0}:{1}".format(self.root_redis_key,
                                                                          entity_name))
        # Redis Key for this Entity
        self.entity_key = "{0}:{1}:{2}".format(self.root_redis_key,
                                               entity_name,
                                               redis_incr_value)

        

    def generate(self):
        """
        Method is stub, child classes should override this method
        """
        pass

    def __add_attribute__(self,attribute,values):
        """
        Helper method takes a rda Core attribute and depending on
        existence of attribute in the datastore and the number of values,
        either creates a new hash value for the entity key, creates a
        list or sorted list based on the attribute, or creates a list, or
        sorted list from the pre-existing value with the values currently
        being ingested into datastore.

        :param attribute: RDA Core attribute name
        :param values: A list of values, if len < 2, list is decomposed into
                       string attribute for entity, otherwise create a set or
                       sorted set
        """
        # Create a key for the set representing this attribute
        attribute_set_key = '{0}:{1}'.format(self.entity_key,attribute)

        # Checks if existing attribute is a hash value
        existing_attribute = self.redis_server.hget(self.entity_key,
                                                    attribute)
        if existing_attribute is not None:
            # Add existing attribute to the new set, remove from entity's hash
            self.redis_server.sadd(attribute_set_key,existing_attribute)
            self.redis_server.hdel(self.entity_key,attribute)
        else:
            # If there is only value, create hash key-value for the entity based
            # attibute value
            if len(values) == 1:
                self.redis_server.hset(self.entity_key,
                                       attribute,
                                       values[0])
            else:
                # Creates a set of all values in list
                self.redis_server.sadd(attribute_set_key,values)
                
                
            

class CreateRDACoreExpressionFromMARC(CreateRDACoreEntityFromMARC):

    def __init__(self,**kwargs):
        kwargs["entity"] = "Expression"
        super(CreateRDACoreExpressionFromMARC,self).__init__(**kwargs)
        

    def generate(self):
        self.__content_type__()

    def __content_type__(self):
        content_types = []
        content_type_key = self.redis_server.hget(self.entity_key,
                                                  "contentType")
        if content_type_key is None:
            content_type_key = "{0}:contentType".format(self.entity_key)
        field336s = self.marc_record.get_fields('336')
        for field in field336s:
            subfld_2 = field.get_subfields('2')
            if len(subfld_2) > 0:
                if subfld_2[0] == 'marccontent':
                    subfld_vals = ''.join(field.get_subfields('a','b'))
                    content_types.append(subfld_vals)
        if len(content_types) > 0:
            for content_type in content_types:
                self.redis_server.sadd(content_type_key,content_type)
        process_tag_list_as_set(self.marc_record,
                                content_type_key,
                                self.redis_server,
                                [('130','h'),
                                 ('730','h'),
                                 ('830','h'),
                                 ('240','h'),
                                 ('243','h'),
                                 ('700','h'),
                                 ('800','h'),
                                 ('710','h'),
                                 ('810','h'),
                                 ('711','h'),
                                 ('811','h')])
        
        
                                                    
        


class CreateRDACoreItemFromMARC(CreateRDACoreEntityFromMARC):

    def __init__(self,**kwargs):
        kwargs["entity"] = "Item"
        super(CreateRDACoreItemFromMARC,self).__init__(**kwargs)

    def generate(self):
        self.__restrictions_on_use__()

    def __restrictions_on_use__(self):
        """
        Extracts any restrictions on use for the Item (this is actually an
        RDA Enchanced attribute and not part of the RDACore
        """
        restriction_on_use_key = self.redis_server.hget(self.entity_key,
                                                        "restrictionsOnUse")
        if restriction_on_use_key is None:
            restriction_on_use_key = "{0}:restrictionsOnUse".format(self.entity_key)
        process_tag_list_as_set(self.marc_record,
                                restriction_on_use_key,
                                self.redis_server,
                                [('540','a'),
                                 ('540','b'),
                                 ('540','c'),
                                 ('540','d'),
                                 ('540','u')])
        
        

class CreateRDACoreManifestationFromMARC(CreateRDACoreEntityFromMARC):

    def __init__(self,**kwargs):
        kwargs["entity"] = "Manifestation"
        super(CreateRDACoreManifestationFromMARC,self).__init__(**kwargs)        
        
        
    def generate(self):
        self.__copyright_date__()
        self.__edition_statement__()
        self.__identifiers__()
        self.__manufacture_statement__()
        self.__production_statement__()
        self.__publication_statement__()
        self.__statement_of_responsiblity__()
        self.__title_proper__()

    def __copyright_date__(self):
        """
        Extracts and sets copyright date from MARC record
        """
        copyright_set_key = self.redis_server.hget(self.entity_key,
                                                   "copyrightDate")
        if copyright_set_key is None:
            copyright_set_key = "{0}:copyrightDate".format(self.entity_key)
        field008 = self.marc_record['008']
        field008_values = list(field008.value())
        # Copyright set for monographs
        if field008_values[6] == 's' or\
           field008_values[6] == 't':
            process_008_date(self.marc_record,
                             self.redis_server,
                             copyright_set_key)
        field260s = self.marc_record.get_fields('260')
        for field in field260s:
            subfield_c = field.get_subfields('c')
            for subfield in subfield_c:
                if subfield.startswith('c'):
                    self.redis_server.zadd(copyright_set_key,
                                           int(subfield[1:]),
                                           subfield[1:])
        process_tag_list_as_set(self.marc_record,
                                copyright_set_key,
                                self.redis_server,
                                [('542','g')],
                                is_sorted=True)        

    def __edition_statement__(self):
        """
        Extracts and sets Edition statement from MARC record
        """
        field250s = self.marc_record.get_fields('250')
        edition_stmt_key = "{0}:editionStatement".format(self.entity_key)
        for field in field250s:
            subfield_a = field.get_subfields('a')
            if len(subfield_a) > 0:
                edition_designation = self.redis_server.hget(edition_stmt_key,
                                                             "designationOfEdition")
                if edition_designation is None:
                    edition_designation = "{0}:designations".format(edition_stmt_key)
                self.redis_server.sadd(edition_designation,
                                       ''.join(subfield_a))
                self.redis_server.hset(edition_stmt_key,
                                       "designationOfEdition",
                                       edition_designation)
            subfield_b = field.get_subfields('b')
            if len(subfield_b) > 0:
                named_revision = self.redis_server.hget(edition_stmt_key,
                                                        "designationOfNamedRevisionOfEdition")
                
                if named_revision is None:
                    named_revision = "{0}:namedRevisions".format(edition_stmt_key)
                self.redis_server.sadd(named_revision,
                                       ''.join(subfield_b))
                self.redis_server.hset(edition_stmt_key,
                                       "designationOfNamedRevisionOfEdition",
                                       named_revision)

    def __identifiers__(self):
        """
        Extracts and sets Manifestation's identifiers from MARC record
        """
        identifiers_set_key = self.redis_server.hget(self.entity_key,
                                                     "identifier")
        if identifiers_set_key is None:
            identifiers_set_key = "{0}:identifiers".format(self.entity_key)
        # get/set ISBN
        process_identifier(self.marc_record,
                           self.redis_server,
                           '020',
                           identifiers_set_key,
                           ['a','z'],
                           "isbn")
        # get/set ISSN
        process_identifier(self.marc_record,
                           self.redis_server,
                           '022',
                           identifiers_set_key,
                           ['a','y','z'],
                           "issn")
        # get/set ISRC, UPC, ISMN, International Article Number, serial, sources
        # from 024 field
        field024s = self.marc_record.get_fields('024')
        for field in field024s:            
            # ISRC Identifier
            if field.indicators[0] == '0':
                process_identifier(self.marc_record,
                                   self.redis_server,
                                   '024',
                                   identifiers_set_key,
                                   ['a','d','z'],
                                   "isrc")
                    
            # UPC Identifier
            elif field.indicators[0] == '1':
                process_identifier(self.marc_record,
                                   self.redis_server,
                                   '024',
                                   identifiers_set_key,
                                   ['a','d','z'],
                                   "upc")
                    
            # ISMN Identifier 
            elif field.indicators[0] == '2':
                process_identifiers(self.marc_record,
                                    self.redis_server,
                                    '024',
                                    identifiers_set_key,
                                    ['a','d','z'],
                                    "ismn")
                    
            # International Article Number Identifier
            elif field.indicators[0] == '3':
                process_identifiers(self.marc_record,
                                    self.redis_server,
                                    '024',
                                    identifiers_set_key,
                                    ['a','d','z'],
                                    "international-article-numbers")                
                    
            # Serial Item and Contribution Identiifer
            elif field.indicators[0] == '4':
                process_identifiers(self.marc_record,
                                    self.redis_server,
                                    '024',
                                    identifiers_set_key,
                                    ['a','d','z'],
                                    "serial-item-contribution-id")                
            # Source specified in $2
            elif field.indicators[0] == '7':
                raw_sources = field.get_subfields('2')
                for source in raw_sources:
                    process_identifiers(self.marc_record,
                                        self.redis_server,
                                        '024',
                                        identifiers_set_key,
                                        ['a','d','z'],
                                        source)
            # Unspecified type of standard number or code
            elif field.indicators[0] == '8':
                self.redis_server.sadd(identifiers_set_key,
                                       ''.join(field.get_subfields('a','d','z')))
        # get/set fingerprint identifier
        field026s = self.marc_record.get_fields('026')
        for field in field026s:
            field_value = ''.join(field.get_subfields('a','b','c','d','e'))
            fingerprint_schema = field.get_subfields('2')
            if fingerprint_schema.count('fei') > -1:
                fingerprint_key = self.redis_server.hget('fei:values',
                                                         field_values)
                if fingerprint_key is None:
                    fingerprint_key = "fei:{0}".format(self.redis_server.incr("global:fei"))
                    self.redis_server.set(fingerprint_key,field_values)
                    self.redis_server.hset('fei:values',
                                           field_values,
                                           fingerprint_key)
            elif fingerprint_schema.count('stcnf') > -1:
                fingerprint_key = self.redis_server.hget('stcnf:values',
                                                         field_values)
                if fingerprint_key is None:
                    fingerprint_key = "stcnf:{0}".format(self.redis_server.incr("global:stcnf"))
                    self.redis_server.set(fingerprint_key,field_values)
                    self.redis_server.hset('stcnf:values',
                                           field_values,
                                           fingerprint_key)
            else:
                fingerprint_key = self.redis_server.hget('fingerprint-other:values',
                                                         field_values)
                if fingerprint_key is None:
                    fingerprint_key = "fingerprint-other:{0}".format(self.redis_server.incr("global:fingerprint-other"))
                    self.redis_server.set(fingerprint_key,field_values)
                    self.redis_server.hset('fingerprint-other:values',
                                           field_values,
                                           fingerprint_key)
            self.redis_server.sadd(identifiers_set_key,
                                   fingerprint_key)
        # Standard technical report number
        process_identifier(self.marc_record,
                           self.redis_server,
                           '027',
                           identifiers_set_key,
                           ['a','z'],
                           "standard-tech-report")
        # Videorecording and other publisher number
        field028s = self.marc_record.get_fields('028')
        for field in field028s:
            if field.indicators[0] == '4':
                process_identifier(self.marc_record,
                                   self.redis_server,
                                   '028',
                                   identifiers_set_key,
                                   ['a'],
                                   "videorecording-number")
            elif field.indicators[0] == '5':
                process_identifier(self.marc_record,
                                   self.redis_server,
                                    '028',
                                   identifiers_set_key,
                                   ['a'],
                                   "other-publisher-number")
        # CODEN
        process_identifier(self.marc_record,
                           self.redis_server,
                           '030',
                           identifiers_set_key,
                           ['a','z'],
                           "coden")
        # Stock number
        process_identifier(self.marc_record,
                           self.redis_server,
                           '037',
                           identifiers_set_key,
                           ['a'],
                           "stock-number")
        # GPO Item number
        process_identifier(self.marc_record,
                           self.redis_server,
                           '074',
                           identifiers_set_key,
                           ['a','z'],
                           "gpo-item")
        # SUDOC, Gov't of Canada, or other
        field086s = self.marc_record.get_fields('086')
        for field in field086s:
            if field.indicators[0] == '0':
                process_identifier(self.marc_record,
                                   self.redis_server,
                                   '086',
                                   identifiers_set_key,
                                   ['a','z'],
                                   'sudoc')
            elif field.indicators[0] == '1':
                process_identifier(self.marc_record,
                                   self.redis_server,
                                   '086',
                                   identifiers_set_key,
                                   ['a','z'],
                                   'canada-gov')
            else:
                source = field.get_subfield('2')
                if len(source) > 0:
                    process_identifier(self.marc_record,
                                       self.redis_server,
                                       '086',
                                       identifiers_set_key,
                                       ['a','z'],
                                       source[0])
        # Report number
        process_identifier(self.marc_record,
                           self.redis_server,
                           '088',
                           identifiers_set_key,
                           ["a","z"],
                           "report-number")
        # Dissertation identifier
        process_identifier(self.marc_record,
                           self.redis_server,
                           '502',
                           identifiers_set_key,
                           ["o"],
                           "dissertation-idenitifer")
        

    def __manufacture_statement__(self):
        manufacture_stmt_key = "{0}:manufactureStatement".format(self.entity_key)
        place_set_key = self.redis_server.hget(manufacture_stmt_key,
                                               "placeOfManufacture")
        if place_set_key is None:
            place_set_key = "{0}:places".format(manufacture_stmt_key)
            self.redis_server.hget(manufacture_stmt_key,
                                   "placeOfManufacture",
                                   place_set_key)
        process_tag_list_as_set(self.marc_record,
                                place_set_key,
                                self.redis_server,
                                [('260','e'),
                                 ('542','k')])
        name_set_key = self.redis_server.hget(manufacture_stmt_key,
                                              "manufactureName")
        if name_set_key is None:
            name_set_key = "{0}:names".format(manufacture_stmt_key)
            self.redis_server.hget(manufacture_stmt_key,
                                   "manufactureName")
        process_tag_list_as_set(self.marc_record,
                                name_set_key,
                                self.redis_server,
                                [('260','f'),
                                 ('542','k')])
        date_sort_key = self.redis_server.hget(manufacture_stmt_key,
                                               "dateOfManufacture")
        if date_sort_key is None:
            date_sort_key = "{0}:dates" % manufacture_stmt_key
            self.redis_server.hset(manufacture_stmt_key,
                                   "dateOfManufacture",
                                   date_sort_key)
        process_008_date(self.marc_record,
                         self.redis_server,
                         date_sort_key)
        

    def __production_statement__(self):
        # Production Statement
        production_stmt_key = "{0}:productionStatement".format(self.entity_key)
        date_sort_key = self.redis_server.hget(production_stmt_key,
                                               "dateOfProduction")
        if date_sort_key is None:
            date_sort_key = "{0}:dates" % production_stmt_key
            self.redis_server.hset(production_stmt_key,
                                   "dateOfProduction",
                                   date_sort_key)
        process_008_date(self.marc_record,
                         self.redis_server,
                         date_sort_key)
        process_tag_list_as_set(self.marc_record,
                                date_sort_key,
                                self.redis_server,
                                [('260','c'),
                                 ('542','j')],
                                is_sorted=True)

    def __publication_statement__(self):
        # Publication Statement
        pub_stmt_key = "{0}:publicationStatement".format(self.entity_key)
        place_set_key = self.redis_server.hget(pub_stmt_key,
                                               "placeOfPublication")
        if place_set_key is None:
            place_set_key = "{0}:places".format(pub_stmt_key)
            self.redis_server.hget(pub_stmt_key,
                                   "placeOfPublication",
                                   place_set_key)
        process_tag_list_as_set(self.marc_record,
                                place_set_key,
                                self.redis_server,
                                [('260','a'),
                                 ('542','k'),
                                 ('542','p')])    
        pub_name_set_key = self.redis_server.hget(pub_stmt_key,
                                                  "publisherName")
        if pub_name_set_key is None:
            pub_name_set_key = "{0}:publishers".format(pub_stmt_key)
            self.redis_server.hset(pub_stmt_key,
                                   "publisherName",
                                   pub_name_set_key)
        process_tag_list_as_set(self.marc_record,
                                pub_name_set_key,
                                self.redis_server,
                                [('260','b'),
                                 ('542','k')])
        pub_date_key = self.redis_server.hget(pub_stmt_key,
                                              "dateOfPublication")
        if pub_date_key is None:
            pub_date_key = "{0}:dates".format(pub_stmt_key)
            self.redis_server.hset(pub_stmt_key,
                                   "dateOfPublication",
                                   pub_date_key)
        process_008_date(self.marc_record,
                         self.redis_server,
                         date_sort_key)
        

    def __title_proper__(self):
        self.redis_server.hset(self.entity_key,
                               "titleProper",
                          self.marc_record.title())
        
    def __statement_of_responsiblity__(self):
        # Statement of Responsibility
        field245s = marc_record.get_fields('245')
        statement_str = ''
        for field in field245s:
            subfield_c = field.get_subfields('c')
            statement_str += "".join(subfield_c)
            if len(statement_str) > 0:
                redis_server.hset(entity_key,
                                  "statementOfResponsibility",
                                  statement_str)

    
    
        

def create_manifestation(marc_record,entity_key):
    """
    Ingests a RDA Core Manifestation into Redis datastore

    :param marc_record: MARC Record
    :param entity_key: Redis key for the Manifestation
    """
    if volatile_redis is None:
        raise ValueError("Volatile Redis not available")
    redis_server = volatile_redis
    
def process_identifier(marc_record,
                       redis_server,
                       field_tag,
                       identifiers_set_key,
                       subfields_list,
                       ident_root):
    """
    Helper function extracts values from the field's subfields, checks to
    see if the subfield value is in the ident's values hash, gets/adds identifier tp
    the entity's identifiers set

    :param marc_record: MARC record
    :param redis_server: Redis server
    :param field_tag: MARC Field tag, i.e. 020, 028
    :param identifiers_set_key: Key for the entity's identifiers set
    :param subfields_list: List of subfields to check
    :param ident_root: Root of the entity
    """
    all_fields = marc_record.get_fields(field_tag)
    for field in all_fields:
        for subfield in field.get_subfields(subfields_list):
            identifier_key = redis_server.hget("{0}:values".format(ident_root),
                                               subfield)
            if identifier_key is None:
                identifier_key = "{0}:{1}".format(ident_root,
                                                  redis_server.incr("global:{0}".format(ident_root)))
                
                self.redis_server.set(identifier_key,subfield)
                redis_server.hset("{0}:values".format(ident_root),
                                  subfield,
                                  identifier_key)
            redis_server.sadd(identifiers_set_key,identifier_key)

def process_008_date(marc_record,redis_server,date_sort_key):
    """
    Helper function extracts dates from 008 MARC field and
    saves to Redis datastore

    :param marc_record: MARC record
    :param redis_server: Redis datastore instance
    :param date_sort_key: Redis date sort key
    """
    field008 = marc_record['008']
    if field008 is not None:
        field_values = list(field008.value())
        date1 = ''.join(field_values[7:11])
        date2 = ''.join(field_values[11:15])
        if len(date1.strip()) > 0:
            redis_server.zadd(date_sort_key,
                              int(date1),
                              date1)
        if len(date2.strip()) > 0:
            redis_server.zadd(date_sort_key,
                              int(date2),
                              date2)
            
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
