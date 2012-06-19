"""
 :mod:`frbr_redis` Module ingests MARC records into a FRBR-Redis datastore 
 controlled by the MARC Batch app. This Module initially ingests the RDA
 core elements from MARC into datastore.
"""
__author__ = 'Jeremy Nelson'
import pymarc,redis,logging,sys
import re,datetime
from marc_batch.fixures import json_loader


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

year_re = re.compile(r"(\d+)")

class MARCRules(object):

    def __init__(self,**kwargs):
        self.json_results = {}
        if kwargs.has_key('json_file'):
            self.json_rules = json_loader[kwargs.get('json_file')]
        if kwargs.has_key('json_rules'):
            self.json_rules = kwargs.get('json_rules')

    def __get_position_values__(self,rule,marc_field):
        """
        Helper method checks MARC values from fixed positions based
        on the rule's position
        """
        values = str()
        if rule.has_key("positions") and marc_field.is_control_field():
            raw_value = marc_field.value()
            positions = rule["positions"]
            for position in positions:
                values += raw_value[int(position)]
        if len(values) < 1:
            return None
        return values

    def __get_subfields__(self,rule,marc_field):
        """
        Helper method extracts any subfields that match pattern
        in the rule's subfield

        :param rule: JSON Rule
        :param marc_field: MARC field
        """
        if rule.has_key("subfields") and hasattr(marc_field,'subfields'):
            rule_subfields = rule["subfields"]
            marc_subfields = marc_field.get_subfields(",".join(rule_subfields))
            return ''.join(marc_subfields)
        return None


    def __test_indicators__(self,rule,marc_field):
        """
        Helper method checks the MARC field indicator againest the
        rule values
        
        :param rule: JSON Rule
        :param marc_field: MARC field
        """
        pass_rule = None
        if rule.has_key("indicators"):
            indicator0,indicator1 = marc_field.indicators
            if rule["indicators"].has_key("0"):
                if rule["indicators"]["0"].count(indicator0) > -1:
                    pass_rule = True
            if rule["indicators"].has_key("1"):
                if rule["indicators"]["1"].count(indicator1) > -1:
                    pass_rule = True
            if pass_rule is None:
                pass_rule = False
        return pass_rule

    def __test_position_values__(self,rule,marc_field):
        """
        Helper method checks MARC values from fixed positions based
        on the rule's position
        """
        pass_rule = None
        if rule.has_key("positions"):
            raw_value = marc_field.value()
            positions = rule["positions"].keys()
            for position in positions:
                conditions = rule["positions"][position]
                position_value = raw_value[int(position)]
                if conditions.count(position_value) > -1:
                    pass_rule = True
            if pass_rule is None:
                pass_rule = False
        return pass_rule

    def load_marc(self,marc_record):
        """
        Method takes a MARC record and applies all of its rules
        to the MARC file. If a MARC field matches the rule's condition,
        the result is saved to json results dict.

        :param marc_record: MARC record
        """
        for rda_element in self.json_rules.keys():
            rule_fields = self.json_rules[rda_element].keys()
            for tag in rule_fields:
                marc_fields = marc_record.get_fields(tag)
                if len(marc_fields) > 0:
                    rule = rule_fields[tag]
                    # Check if indicators are in rule, check
                    # and apply to MARC field
                    for field in marc_fields:
                        test_indicators = self.__test_indicators__(rule,field)
                        if test_indicators is False:
                            pass
                        # For fixed fields
                        test_position = self.__test_position_values__(rule,field)
                        # For variable fields
                        subfield_values = self.__get_subfields__(rule,field)
                        if subfields_values is not None:
                            if self.json_results.has_key(rda_element):
                                self.json_results[rda_element].append(subfields_values)
                            else:
                                self.json_results[rda_element] = subfields_values
                                
                        
                        
                        
                    
            

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
                                       ''.join(values))
            else:
                # Creates a set of all values in list
                for row in values:
                    self.redis_server.sadd(attribute_set_key,row)
                
                
            

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
        self.__carrier_type__()
        self.__copyright_date__()
        self.__edition_statement__()
        self.__identifiers__()
        self.__manufacture_statement__()
        self.__production_statement__()
        self.__publication_statement__()
        self.__statement_of_responsiblity__()
        self.__title_proper__()

    def __carrier_type__(self):
        """
        Extracts Carrier Type from MARC record
        """
        field007 = self.marc_record['007']
        if field007 is not None:
            field_value = field007.value()
            position0,position1 = field_value[0],field_value[1]
            # Load json dict mapping MARC 007 position 0 and 1 to RDA Carrier Types
            carrier_types_dict = json_loader.get('marc-carrier-types')
            if carrier_types_dict.has_key(position0):
                if carrier_types_dict[position0].has_key(position1):
                    self.__add_attribute__('carrierType',
                                           [carrier_types_dict[position0][position1],])
        # Adds type of unit in MARC 300 $f
        field300s = self.marc_record.get_fields('300')
        for field in field300s:
            subfield_f = field.get_subfields('f')
            self.__add_attribute__('carrierType',
                                   [''.join(subfield_f),])
        # Adds RDA MARC 338 w/conditional
        field338s = self.marc_record.get_fields('338')
        for field in field338s:
            subfield_2 = ''.join(field.get_subfields('2'))
            if subfield_2.count('marcmedia') > -1:
                for subfield in field.get_subfields('a','b'):
                    self.__add_attribute__('carrierType',
                                           [subfield,])
                    
                
            

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
                    year_search = year_re.search(subfield)
                    if year_search is not None:
                        self.redis_server.zadd(copyright_set_key,
                                               int(year_search.groups()[0]),
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
                source = field.get_subfields('2')
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
        process_tag_list_as_set(self.marc_record,
                                place_set_key,
                                self.redis_server,
                                [('260','e'),
                                 ('542','k')])
        name_set_key = self.redis_server.hget(manufacture_stmt_key,
                                              "manufactureName")
        if name_set_key is None:
            name_set_key = "{0}:names".format(manufacture_stmt_key)
        process_tag_list_as_set(self.marc_record,
                                name_set_key,
                                self.redis_server,
                                [('260','f'),
                                 ('542','k')])
        date_sort_key = self.redis_server.hget(manufacture_stmt_key,
                                               "dateOfManufacture")
        if date_sort_key is None:
            date_sort_key = "{0}:dates".format(manufacture_stmt_key)
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
            date_sort_key = "{0}:dates".format(production_stmt_key)
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
            self.redis_server.hset(pub_stmt_key,
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
                         pub_date_key)
        

    def __title_proper__(self):
        self.redis_server.hset(self.entity_key,
                               "titleProper",
                               self.marc_record.title())
        
    def __statement_of_responsiblity__(self):
        # Statement of Responsibility
        field245s = self.marc_record.get_fields('245')
        statement_str = ''
        for field in field245s:
            subfield_c = field.get_subfields('c')
            statement_str += "".join(subfield_c)
            if len(statement_str) > 0:
                self.redis_server.hset(self.entity_key,
                                       "statementOfResponsibility",
                                       statement_str)

class CreateRDACorePersonFromMARC(object):

    def __init__(self,**kwargs):
        if kwargs.has_key('json-rules'):
            self.json_rules = kwargs.get('json-rules')
        else:
            self.json_rules = json_loader['marc-rda-person']

    def load(self):
        for rda_element in self.json_rules.keys():
            marc_fields = rda_element.keys()
            for field in marc_fields:
                if field.has_key("indicators"):
                    for indicator in field["indicators"]:
                        pass
                    

class CreateRDACoreWorkFromMARC(CreateRDACoreEntityFromMARC):

    def __init__(self,**kwargs):
        kwargs["entity"] = "Work"
        super(CreateRDACoreWorkFromMARC,self).__init__(**kwargs)
        

    def generate(self):
        self.__date_of_work__()
        self.__form_of_work__()
        self.__identifier_for_the_work__()
        self.__title_of_work__()
        


    def __date_of_work__(self):
        redis_key = "{0}:dateOfWork".format(self.entity_key)
        process_tag_list_as_set(self.marc_record,
                                redis_key,
                                self.redis_server,
                                [('130','a'),
                                 ('240','a'),
                                 ('240','d'),
                                 ('240','f')],
                                is_sorted=True)

    def __form_of_work__(self):
        redis_key = "{0}:formOfWork".format(self.entity_key)
        process_tag_list_as_set(self.marc_record,
                                redis_key,
                                self.redis_server,
                                [('130','a'),
                                 ('240','a'),
                                 ('243','a'),
                                 ('380','a'),
                                 ('700','t'),
                                 ('710','t'),
                                 ('711','t'),
                                 ('730','a'),
                                 ('800','t'),
                                 ('810','t'),
                                 ('811','a'),
                                 ('830','a')])

    def __identifier_for_the_work__(self):
        redis_key = "{0}:identifier".format(self.entity_key)
        field024s = self.marc_record.get_fields('024')
        for field in field024s:
            if [7,8].count(int(field.indicators[1])) > -1:
                self.redis_server.sadd(redis_key,
                                       ''.join(field.get_subfields("a","d","z")))
        process_tag_list_as_set(self.marc_record,
                                redis_key,
                                self.redis_server,
                                [('130','0'),
                                 ('240','0'),
                                 ('710','0'),
                                 ('711','0'),
                                 ('730','0'),
                                 ('810','0'),
                                 ('811','0'),
                                 ('830','0')])
        
               

    def __title_of_work__(self):
        redis_key = "{0}:titleOfWork".format(self.entity_key)
        process_tag_list_as_set(self.marc_record,
                                redis_key,
                                self.redis_server,
                                [('130','a'),
                                 ('240','a'),
                                 ('243','a'),
                                 ('730','a'),
                                 ('830','a')])
    


        

def create_rda_redis(marc_record,datastore):
    """
    Function takes a MARC record and Redis datastore and
    generates a complete rdaCore Work, Expression, Manifestation,
    and Items

    :param marc_record: MARC record
    :param datastore: Redis datastore
    """
    sys.stderr.write(".")
    # Generate a new rdaCore record key
    root_key = "rdaCore:{0}".format(datastore.incr("global rdaCore"))
    work_creator = CreateRDACoreWorkFromMARC(record=marc_record,
                                             redis_server=datastore,
                                             root_redis_key=root_key)
    work_creator.generate()
    datastore.sadd("rdaCore:Works",work_creator.entity_key)
    expression_creator = CreateRDACoreExpressionFromMARC(record=marc_record,
                                                         redis_server=datastore,
                                                         root_redis_key=root_key)
    expression_creator.generate()
    datastore.sadd("rdaCore:Expressions",expression_creator.entity_key)
    manifestation_creator = CreateRDACoreManifestationFromMARC(record=marc_record,
                                                               redis_server=datastore,
                                                               root_redis_key=root_key)
    manifestation_creator.generate()
    datastore.sadd("rdaCore:Manifestations",manifestation.entity_key)
    item_creator = CreateRDACoreItemFromMARC(record=marc_record,
                                             redis_server=datastore,
                                             root_redis_key=root_key)
    item_creator.generate()
    datastore.sadd("rdaCore:Items",item_creator.entity_key)
                              
    
    
def quick_rda(marc_record,datastore):
    """
    Create a quick-and-dirty rdaCore Redis representation of a MARC
    record

    :param marc_record: MARC record
    :param datastore: Redis datastore
    """
    root_key = "rda:{0}".format(datastore.incr("global rdaCore"))
    bib_number = marc_record['907']['a'][1:-1]
    datastore.hset(root_key,"tutt:bib_number",bib_number)
    work_key = "rda:Works:{0}".format(datastore.incr("global rda:Works"))
    datastore.hset(work_key,"record_key",root_key)
    title_key = "rda:Titles:{0}".format(datastore.incr("global rda:Titles"))
    datastore.hset(title_key,'preferredTitle',marc_record.title())
    datastore.hset(work_key,"titleOfWork",title_key)
    expression_key = "rda:Expressions:{0}".format(datastore.incr("global rda:Expressions"))
    datastore.hset(expression_key,"record_key",root_key)
    datastore.hset("rda:ExpressionOfWork",
                   expression_key,
                   work_key)
    datastore.hset("rda:WorkExpressed",
                   work_key,
                   expression_key)
    manifestation_key = "rda:Manifestations:{0}".format(datastore.incr("global rda:Manifestations"))
    datastore.hset(manifestation_key,"record_key",root_key)
    datastore.hset("rda:ManifestationOfWork",                   
                   manifestation_key,
                   work_key)
    datastore.hset("rda:ManifestationOfExpression",
                   manifestation_key,
                   expression_key)
    datastore.hset("rda:ExpressionManifested",
                   expression_key,
                   manifestation_key)
    datastore.hset("rda:WorkManifested",
                   work_key,
                   manifestation_key)
    field008 = marc_record['008']
    if field008 is not None:
        raw_year = field008.value()[7:11]
        datastore.hset(manifestation_key,"copyrightDate",raw_year)
        year_search = year_re.search(raw_year)
        if year_search is not None:
            year = year_search.groups()[0]
            datastore.zadd("rda:SortedCopyrightDates",int(year),manifestation_key)
            
    item_key = "rda:Items:{0}".format(datastore.incr('global rda:Items'))
    datastore.hset(item_key,"record_key",root_key)
    datastore.hset("rda:ExemplarOfManifestation",
                   item_key,
                   manifestation_key)
    datastore.hset("rda:ManifestationExemplified",
                   manifestation_key,
                   item_key)
    
                                            
    
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
            date_search = year_re.search(date1)
            if date_search is not None:
                redis_server.zadd(date_sort_key,
                                  int(date_search.groups()[0]),
                                  date1)
        if len(date2.strip()) > 0:
            date_search = year_re.search(date2)
            if date_search is not None:                
                redis_server.zadd(date_sort_key,
                                  int(date_search.groups()[0]),
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
                    year_search = year_re.search(subfield)
                    if year_search is not None:
                        redis_server.zadd(redis_key,
                                          int(year_search.groups()[0]),
                                          subfield)
                else:
                    redis_server.sadd(redis_key,subfield)
    
            
            
                
                                  
    
    

def ingest_record(marc_record):
    if volatile_redis is None:
        print("Volatile Redis not available")
        return None
    redis_server = volatile_redis
    bib_number = marc_record['907']['a'][1:-1]
    redis_id = redis_server.incr("global:rdaCore")
    redis_key = "rdaCore:%s" % redis_id
    CreateRDACoreWorkFromMARC(record=marc_record,
                              redis_server=redis_server,
                              root_redis_key=redis_key)
    


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
