"""
 :mod:`ingesters` Module ingests MARC21 and MODS records into a BIBFRAME-Redis datastore
 controlled by the BIBFRAME app.
"""
__author__ = "Jeremy Nelson"

import datetime
import logging
import json
import marc21_facets
import os
import pymarc 
import re
import redis
import sys
import time
from bibframe.models import Annotation, Organization, Work, Holding, Instance
from bibframe.models import Person, Book, Cartography, Manuscript, Map, MixedMaterial  
from bibframe.models import MovingImage, MusicalAudio, NonmusicalAudio  
from bibframe.models import NotatedMusic, SoftwareOrMultimedia, StillImage
from bibframe.models import RemoteSensingImage, Title, ThreeDimensionalObject
from bibframe.ingesters.Ingester import Ingester
from bibframe.ingesters import tutt_maps, marc21_maps, web_services
from bibframe.ingesters.bibframeMARCParser import MARCParser
from discovery.redis_helpers import slug_to_title
from django.template.defaultfilters import slugify
from call_number.redis_helpers import generate_call_number_app
from person_authority.redis_helpers import get_or_generate_person
from aristotle.settings import IS_CONSORTIUM, PROJECT_HOME
from organization_authority.redis_helpers import get_or_add_organization
from title_search.redis_helpers import generate_title_app, process_title
from title_search.redis_helpers import index_title, search_title
from keyword_search.whoosh_helpers import index_marc


from lxml import etree
from rdflib import RDF, RDFS, Namespace

from bibframe.classifiers import simple_fuzzy

import aristotle.settings as settings
from aristotle.settings import REDIS_DATASTORE


field007_lkup = json.load(open(os.path.join(PROJECT_HOME,
                                            "bibframe",
                                            "fixures",
                                            "marc21-007.json"),

                                "rb"))


ADDITIVE_SUBFLD_RE = re.compile("[+$](?P<subfld>\w)")
CONDITIONAL_SUBFLD_ID_RE = re.compile(r'[+](?P<indicator2>\w)"(?P<fld_value>\w+)"')
IND_CONDITIONAL_RE = re.compile(r'if i(?P<indicator>\w)=(?P<test>\w)')
PRECEDE_RE = re.compile(r'precede \w+ with "(?P<prepend>\w+:*)')
COMBINED_SUBFLD_RE = re.compile(r'[$](?P<subfld>\w)[+]*')
SUBFLD_RE = re.compile(r"[$|/|,](?P<subfld>\w)")
SINGLE_TAG_IND_RE = re.compile(r'(\d{3})(\d|[-])(\d|[-])')
RULE_ONE_RE = re.compile(r"\d{3},*-*\s*[$|/](?P<subfld>\w)$")
RULE_TWO_RE = re.compile(r"\d{3},*-*\s*[$|/](?P<subfld>\w)[+]*")
TAGS_RE = re.compile(r"(?P<tag>\d{3}),*-*")

MARC_FLD_RE = re.compile(r"(\d+)([-|w+])([-|w+])/(\w+)")

class MARC21Helpers(object):
    """
    MARC21 Helpers for MARC21 Ingester classes
    """
    marc_fld_re = re.compile(r"(\d+)(--)*([//].+)*[,]*")

    def __init__(self,marc_record):
        self.record = marc_record
      
                
    def getSubfields(self,tag,*subfields):
        """
        Extracts values from a MARC Variable Field

        :param tag: MARC21 tag
        :param subfields: one or more subfields
        """
        if self.record[tag] is not None:
            field = self.record[tag]
            return ' '.join(field.get_subfields(*subfields))

class MARC21IngesterException(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "MARC21IngesterException Error={0}".format(self.value)


class MARC21Ingester(Ingester):
    "Base RLSP BIBFRAME Ingester class for a MARC21 Record"
    

    def __init__(self, **kwargs):
        """Creates an Ingester with basic parameters

        Keywords:
        record -- MARC21 Record
        redis_datastore -- Single Redis instance or Redis Cluster 
        """
        self.record = kwargs.get('record', None)
        self.redis_datastore = kwargs.get('redis_datastore', None)
        self.entity_info = {}

    def __extract__(self,**kwargs):
        """
        Helper function takes a tag and list of rules and returns 
        either a set or a string of values 

        :kwarg tags: A list of MARC21 tags
        :kwarg indict1: A rule for indicator 1
        :kwarg indict2: A rule for indicator 2
        :kwarg subfields: A list of subfields
        """
        output, fields = [], []
        tags = kwargs.get('tags', None)
        if tags is None:
            raise MARC21IngesterException("__extract__ helper function requires at least one MARC21 field tag")
        indicator1_rule = kwargs.get('indict1', None)
        indicator2_rule = kwargs.get('indict2', None)
        subfields = kwargs.get('subfields', None)
        for tag in tags:
            fields.extend(self.record.get_fields(tag))
        for field in fields:
            if indicator1_rule is not None:
                if not eval(indicator1_rule,field.indicator1):
                   continue
            if indicator2_rule is not None:
                if not eval(indicator2_rule,field.indicator2):
                    continue
            
            for subfield in subfields:
                output.extend(field.get_subfields(subfield))
        if len(output) == 1:
            return output[0]
        elif len(output) > 1:
            
            return set(output)    

    def __rule_one__(self, rule, in_order=True):
        """Helper method for MARC rule matching

        For MARC21 Rule patterns like:
        '130,730,830,245,246,247,242 $n'
        '222,210 $b'

        Parameters:
        rule -- Text string of MARC21 to BIBFRAME rule
        in_order -- Returns first 
        """
        
        values = []
        rule_result = RULE_ONE_RE.search(rule)
        if rule_result is not None:
            if ADDITIVE_SUBFLD_RE.search(rule) is not None:
                subfields = ADDITIVE_SUBFLD_RE.findall(rule)
            else:
                subfields = [rule_result.group('subfld'),]
            tags = TAGS_RE.findall(rule)
            if in_order is True:
                while 1:
                    if len(tags) < 1:
                        break
                    tag = tags.pop(0)
                    
                    marc_fields = self.record.get_fields(tag)
                    if len(marc_fields) > 0:
                        break
            else:
                marc_fields = []
                for tag in tags:
                    marc_fields.extend(self.record.get_fields(tag))
            if len(marc_fields) > 0:
                for marc_field in marc_fields:
                    if not marc_field.is_control_field():
                        for subfield in subfields:
                            tag_value = marc_field.get_subfields(subfield)
                            tag_value = set(tag_value)
                            if tag_value is not None:
                                values.append(' '.join(tag_value))
        values = list(set(values))
        return values


class MARC21toFacets(MARC21Ingester):
    """
     MARC21toFacets creates a BIBFRAME annotations to be associated with
     either a Work or Instance.
    """

    def __init__(self, **kwargs):
        self.facets = None
        self.creative_work = kwargs.get('creative_work')
        self.instance = kwargs.get('instance')
        super(MARC21toFacets, self).__init__(**kwargs)



    def add_access_facet(self, **kwargs):
        """
        Creates a bibframe:Annotation:Facet:Access based on
        extracted info from the MARC21 Record

        :keyword instance: BIBFRAME Instance, defaults to self.instance
        :keyword record: MARC21 record, defaults to self.marc_record
        """
        instance = kwargs.get("instance", self.instance)
        record = kwargs.get("record", self.record)
        access = marc21_facets.get_access(record)
        facet_key = "bf:Facet:access:{0}".format(slugify(access))
        self.__add_label__(facet_key)
        self.redis_datastore.sadd(facet_key, instance.redis_key)
        self.redis_datastore.sadd("{0}:hasAnnotation".format(instance.redis_key),
                              facet_key)

    def add_format_facet(self, **kwargs):
        """
        Creates a bibframe:Annotation:Facet:Format based on the
        rda:carrierTypeManifestation property of the marcr:Instance

        :keyword instance: BIBFRAME Instance, defaults to self.instance
        """
        # Extract's the Format facet value from the Instance and
        # creates an Annotation key that the instance's redis key
        instance = kwargs.get("instance", self.instance)
        facet_key = "bf:Facet:format:{0}".format(
            slugify(
                getattr(instance,'rda:carrierTypeManifestation')))
        self.redis_datastore.sadd(facet_key, instance.redis_key)
        self.__add_label__(facet_key)
        self.redis_datastore.zadd('bf:Facet:format:sort',
            float(self.redis_datastore.scard(facet_key)),
            facet_key)
        instance_annotation_key = "{0}:hasAnnotation".format(instance.redis_key)
        self.redis_datastore.sadd("{0}:hasAnnotation".format(
            instance.redis_key),
                facet_key)



    
    def add_lc_facet(self, **kwargs):
        """
        Adds bibframe:CreativeWork to the bibframe:Annotation:Facet:LOCLetter
        facet based on extracted info from the MARC21 Record

        :keyword creative_work: BIBFRAME CreativeWork, defaults to
                                self.creative_work
        :keyword record: MARC21 record, defaults to self.marc_record
        """
        creative_work = kwargs.get('creative_work', self.creative_work)
        record = kwargs.get('record', self.record)
        lc_facet, lc_facet_desc = marc21_facets.get_lcletter(record)
        for row in lc_facet_desc:
            facet_key = "bf:Facet:loc-first-letter:{0}".format(
                slugify(lc_facet))
            self.redis_datastore.sadd(facet_key, creative_work.redis_key)
            self.redis_datastore.sadd("{0}:hasAnnotation".format(
                creative_work.redis_key),
                facet_key)
            self.redis_datastore.hset(
                "bf:Facet:labels",
                facet_key,
                row)
            self.redis_datastore.zadd(
                "bf:Facet:loc-first-letter:sort",
                float(self.redis_datastore.scard(facet_key)),
                facet_key)
            self.redis_datastore.sadd("{0}:hasAnnotation".format(
                creative_work.redis_key),
                facet_key)

    def add_language_facet(self, **kwargs):
        """
        Method takes an instance and adds to
        bf:Facet:language facet
        """
        instance = kwargs.get('instance', self.instance)
        language = self.redis_datastore.hget(instance.redis_key,
                                             'language')
        if language is not None:
            facet_key = 'bf:Facet:language:{0}'.format(
                slugify(language))
            self.redis_datastore.sadd(facet_key, instance.redis_key)
            self.redis_datastore.hset('bf:Facet:labels',
                                      facet_key,
                                      language)
            instance_annotation_key = "{0}:hasAnnotation".format(
                instance.redis_key)
            self.redis_datastore.zadd(
                'bf:Facet:language:sort',
                float(self.redis_datastore.scard(facet_key)),
                facet_key)
            self.redis_datastore.sadd(instance_annotation_key,
                                      facet_key)

    def add_locations_facet(self, **kwargs):
        """
        Method takes an instance and a MARC21 record, extracts all CC's
        location (holdings) codes from the MARC21 record and adds the instance
        key to all of the holdings facets.

        :param instance: BIBFRAME Instance, defaults to self.instance
        :param record: MARC21 record, defaults to self.marc_record
        """
        instance = kwargs.get("instance", self.instance)
        record = kwargs.get("record", self.record)
        if hasattr(settings, "IS_CONSORTIUM"):
            consortium = settings.IS_CONSORTIUM
        else:
            consortium = False
        if consortium is True:
            output = marc21_facets.get_carl_location(record)
            if len(output) > 0:
                redis_key = "bf:Facet:location:{0}".format(
                    output.get("site-code"))
                self.redis_datastore.sadd(redis_key, instance.redis_key)
                self.redis_datastore.hset(instance.redis_key,
                                      "ils-bib-number",
                                      output.get('ils-bib-number'))
                self.redis_datastore.hset(instance.redis_key,
                                      "ils-item-number",
                                      output.get('ils-item-number'))
                self.redis_datastore.zadd("bf:Facet:locations:sort",
                                        float(self.redis_datastore.scard(redis_key)),
                                        redis_key)
        else:
            locations = marc21_facets.get_cc_location(record)
            if len(locations) > 0:
                for location in locations:
                    redis_key = "bf:Facet:location:{0}".format(
                        slugify(location[1]))
                    self.redis_datastore.sadd(redis_key, instance.redis_key)
                    if not self.redis_datastore.hexists(
                        "bf:Facet:labels",
                        slugify(location[1])):
                        self.redis_datastore.hset(
                            "bf:Facet:labels",
                            redis_key,
                            location[1])
                    self.redis_datastore.zadd(
                        "bf:Facet:locations:sort",
                        float(self.redis_datastore.scard(redis_key)),
                        redis_key)
                    self.redis_datastore.sadd("{0}:hasAnnotation".format(instance.redis_key),
                                          redis_key)

    def add_publish_date_facet(self, **kwargs):
        """
        Method adds the publication date of the instance to the
        bf:Facet:pub-year:{year}
        """
        instance = kwargs.get('instance', self.instance)
        publish_year = self.redis_datastore.hget(
            instance.redis_key,
            'rda:dateOfPublicationManifestation')
        if publish_year is not None:
            facet_key = 'bf:Facet:pub-year:{0}'.format(publish_year)
            self.redis_datastore.sadd(facet_key, instance.redis_key)
            self.redis_datastore.hset('bf:Facet:labels',
                                      facet_key,
                                      publish_year)
            instance_annotation_key = "{0}:hasAnnotation".format(
                instance.redis_key)
            self.redis_datastore.zadd(
                'bf:Facet:pub-year:sort',
                float(self.redis_datastore.scard(facet_key)),
                facet_key)
            self.redis_datastore.sadd(instance_annotation_key,
                                      facet_key)
                                                 
        

    def ingest(self,**kwargs):
        """
        Method runs all of the Facet generation methods

        :param creative_work: BIBFRAME CreativeWork, defaults to self.creative_work
        :param instance: BIBFRAME Instance, default to self.instnace
        :param record: MARC21 record, defaults to self.marc_record
        """
        creative_work = kwargs.get('creative_work', self.creative_work)
        instance = kwargs.get("instance", self.instance)
        record = kwargs.get('record', self.record)
        self.add_access_facet(instance=instance,record=record)
        self.add_format_facet(instance=instance)
        self.add_lc_facet(creative_work=creative_work,
            record=record)
        self.add_locations_facet(instance=instance,
                                 record=record)
        
        self.add_publish_date_facet(instance=instance)
        self.add_language_facet(instance=instance)
        

class MARC21toInstance(MARCParser):

    def __init__(self, **kwargs):
        kwargs['rules_filename'] = 'bibframe-instance-map.json'
        super(MARC21toInstance, self).__init__(**kwargs)

        if kwargs.has_key('instanceOf'):
            self.entity_info['instanceOf'] = kwargs.get('instanceOf')

    def add_instance(self):
        self.instance = Instance(redis_datastore=self.redis_datastore)
        for key, value in self.entity_info.iteritems():
            if key is not None and value is not None:
                setattr(self.instance,
                        key,
                        value)
        self.instance.save()
        

    def ingest(self):
        self.parse()
        #! Should do duplication check before calling add_instance
        self.add_instance()

        
class MARC21toBIBFRAME(MARC21Ingester):
    """
    MARC21toBIBFRAME takes a MARC21 record and ingests into BIBFRAME Redis
    datastore
    """

    def __init__(self, **kwargs):
        super(MARC21toBIBFRAME, self).__init__(**kwargs)
        
    def __duplicate_check__(self, redis_key):
        """Based upon type of redis key, checks if MARC Record is a
        duplicate

        Parameters:
        redis_key -- Redis Key
        """
        field907 = self.record['907']
        if field907 is not None:
            if self.redis_datastore.hexists(redis_key,
                                            field907['a'][1:-1]) is True:
                return True
            else:
                return False
        all945s = self.record.get_fields('945')
        for field in all945s:
            a_subfields = field.get_subfields('a')
            for subfield in a_subfields:
                data = subfield.split(" ")
                # Bibnumber already exists return True
                if self.redis_datastore.hexists(redis_key,
                                                data[1]) is True:
                    return True
        return False
    
        
        

    def ingest(self):
        "Method runs a complete ingestion of a MARC21 record into RLSP"
        # Start with either a new or existing Creative Work or subclass
        # like Book, Article, MusicalAudio, or MovingImage
        if self.__duplicate_check__('ils-bib-numbers') is True:
            return
        self.marc2creative_work = MARC21toCreativeWork(
            redis_datastore=self.redis_datastore,
            record=self.record)
        self.marc2creative_work.ingest()
        
        # Exit ingest if a creative work is missing
        if self.marc2creative_work.creative_work is None:
            return
        work_key = self.marc2creative_work.creative_work.redis_key
        # Add work_key to the relatedRole:aut set, should support other
        # roles based on MARC mapping
        if self.marc2creative_work.entity_info.has_key('rda:isCreatedBy'):
            for creator_key in self.marc2creative_work.entity_info.get('rda:isCreatedBy'):
                self.redis_datastore.sadd('{0}:resourceRole:aut'.format(creator_key),
                                          work_key)
        # Extract Instance
        self.marc2instance = MARC21toInstance(
            instanceOf=work_key,
            record=self.record,
            redis_datastore=self.redis_datastore,)
        self.marc2instance.ingest()
        self.marc2instance.instance.save()
        
        finish_instance = datetime.datetime.utcnow()
        instance_key = self.marc2instance.instance.redis_key
        work_instances_key = "{0}:hasInstance".format(work_key)
        if self.redis_datastore.exists(work_instances_key):
            self.redis_datastore.sadd(work_instances_key,
                                      self.marc2instance.instance.redis_key)
        else:
            existing_instance_key = self.redis_datastore.hget(
                work_key,
                'hasInstance')
            # Convert hash value to a set if instance_keys are
            # different
            if existing_instance_key is not None:
                if instance_key != existing_instance_key:
                    # Remove existing instance key from work_key
                    self.redis_datastore.hdel(work_key, 'instanceOf')
                    # Add both instance keys to new work set key
                    self.redis_datastore.sadd(work_instances_key,
                                              instance_key,
                                              existing_instance_key)
            # Set hash value for hasInstance singleton
            else:
                self.redis_datastore.hset(work_key,
                                          'hasInstance',
                                          instance_key)
        index_marc(instance_keys=[instance_key,],
                   record=self.record,
                   redis_datastore=self.redis_datastore,
                   work_key=work_key)
        self.marc2library_holdings = MARC21toLibraryHolding(
            redis_datastore=self.redis_datastore,
            record=self.record,
            instance=self.marc2instance.instance)
        self.marc2library_holdings.ingest()
        instance_annotation_key = "{0}:hasAnnotation".format(
                self.marc2instance.instance.redis_key)
        if self.redis_datastore.hexists(self.marc2instance.instance.redis_key,
                                        'hasAnnotation'):
            annotation = self.marc2instance.instance.hasAnnotation
            self.redis_datastore.hdel(self.marc2instance.instance.redis_key,
                                      'hasAnnotation')
            self.redis_datastore.sadd(instance_annotation_key,
                                      annotation)
        for holding in self.marc2library_holdings.holdings:
            self.redis_datastore.sadd(instance_annotation_key,
                                      holding.redis_key)
        
        generate_call_number_app(self.marc2instance.instance, 
                                 self.redis_datastore)
        self.marc2facets = MARC21toFacets(redis_datastore=self.redis_datastore,
                                          record=self.record,
                                          creative_work=self.marc2creative_work.creative_work,
                                          instance=self.marc2instance.instance)
        self.marc2facets.ingest()


class MARC21toLibraryHolding(MARC21Ingester):
    "Ingests a MARC record into the Redis Library Services Platform"
    

    def __init__(self,**kwargs):
        super(MARC21toLibraryHolding,self).__init__(**kwargs)
        self.holdings = []
        self.is_local = kwargs.get('local', True)
        self.instance = kwargs.get('instance', None)

    def __add_cc_holdings__(self, cc_key='bf:Organization:1'):
        "Helper function for Colorado College MARC Records"
        # Assumes hybrid environment
        if self.redis_datastore.hget('prospector-institution-codes',
                                     '9cocp') is not None:
            cc_key = self.redis_datastore.hget('prospector-institution-codes',
                                     '9cocp')
        
        holding = Holding(redis_datastore=self.redis_datastore)
        self.entity_info['ils-bib-number'] = self.record['907']['a'][1:-1]
        cc_tutt_code = self.record['994']['a']
        if tutt_maps.LOCATION_CODE_MAP.has_key(cc_tutt_code):
            location_key = '{0}:codes:{1}'.format(cc_key,
                                                  cc_tutt_code)
        else:
            location_key = cc_key
        for key, value in self.entity_info.iteritems():
            setattr(holding, key, value)
        setattr(holding, 'schema:contentLocation', location_key)
        if self.instance is not None:
            holding.annotates = self.instance.redis_key
            self.redis_datastore.sadd("{0}:resourceRole:own".format(cc_key),
                                      self.instance.redis_key)
        holding.save()
        if location_key != cc_key:
            # Assumes local location
            self.redis_datastore.sadd(location_key, holding.redis_key)
        if hasattr(holding, 'ils-bib-number'):
            self.redis_datastore.hset('ils-bib-numbers',
                                      getattr(holding, 'ils-bib-number'),
                                      holding.redis_key)
        self.holdings.append(holding)
        
        

    def __add_consortium_holdings__(self):
        "Helper function for CARL Alliance MARC records"
        # quick check if local cc record using 994 field
        if self.record['994'] is not None:
            self.__add_cc_holdings__()
            return
        all945s = self.record.get_fields('945')
        for field in all945s:
            a_subfields = field.get_subfields('a')
            for subfield in a_subfields:
                holding = Holding(redis_datastore=self.redis_datastore)
                data = subfield.split(" ")
                institution_code = data[0]
                org_key = self.redis_datastore.hget(
                    'prospector-institution-codes',
                     institution_code)
                setattr(holding, 'schema:contentLocation', org_key)
                setattr(holding, 'ils-bib-number', data[1])
                setattr(holding, 'ils-item-number', data[2])
                for key,value in self.entity_info.iteritems():
                    setattr(holding, key, value)
                if self.instance is not None:
                    holding.annotates = self.instance.redis_key
                    # Use MARC Relator Code for set key 
                    self.redis_datastore.sadd(
                        "{0}:resourceRole:own".format(org_key),
                        self.instance.redis_key)
                holding.save()
                self.redis_datastore.hset(
                    'ils-bib-numbers',
                    getattr(holding, 'ils-bib-number'),
                    holding.redis_key)
                if self.instance is not None:
                    instance_annotation_key = "{0}:hasAnnotation".format(
                        self.instance.redis_key)
                    self.redis_datastore.sadd(instance_annotation_key,
                                              holding.redis_key)

                self.holdings.append(holding)


    def add_holdings(self):
        """
        Creates one or more Library Holdings based on values in the entity
        """
        if self.is_local is True:
            # CC specific III MARC record format, should be modified to be more
            # generic
            self.__add_cc_holdings__()
        else:
            self.__add_consortium_holdings__()
 

    def ingest(self):
        """
        Ingests a MARC21 record and creates a Library Holding resource that 
        annotates a Creative Work or Instance.
        """
        self.extract_ddc()
        self.extract_govdoc()
        self.extract_lcc()
        self.extract_medical()
        self.extract_cc_local()
        self.extract_udc()
        self.add_holdings()

    def __extract_callnumber__(self, tags):
        """
        Helper function extracts a call number from a resource

        :param tags: One or more MARC21 field tags
        """
        output = []
        fields = self.record.get_fields(*tags)
        for field in fields:
            subfield_b = field['b']
            for subfield in field.get_subfields('a'):
                if subfield_b is not None:
                    output.append("{0} {1}".format(subfield,subfield_b).strip())
                else:
                    output.append(subfield)
        if len(output) == 1:
            return output[0]
        elif len(output) > 1:
            return set(output)
        else:
            return output
       

    def extract_ddc(self):
        """
        Extracts LCC Dewey Decimal call number from a resource
        """
        ddc_values = self.__extract_callnumber__(['082',])
        if len(ddc_values) > 0:
            self.entity_info['callno-ddc'] = ddc_values

    def extract_govdoc(self):
        """
        Extracts Govdoc call number from a resource
        """
        govdocs_values = self.__extract_callnumber__(['086',])
        if len(govdocs_values):
            self.entity_info['callno-govdoc'] = govdocs_values

    def extract_lcc(self):
        """
        Extracts LCC call number from a MARC21 record
        """
        lcc_values = self.__extract_callnumber__(['050',
                                                  '051',
                                                  '055',
                                                  '061',
                                                  '070',
                                                  '071'])
        if len(lcc_values) > 0:
            self.entity_info['callno-lcc'] = lcc_values

    def extract_medical(self):
        med_callnumbers = self.__extract_callnumber__(['060',])
        if len(med_callnumbers) > 0:
            self.entity_info['callno-nlm'] = med_callnumbers

    def extract_cc_local(self):
        """
        Extracts local call number from MARC21 record following Colorado College
        practice
        """
        local_099 = self.record['099']
        if local_099 is not None:
            self.entity_info['callno-local'] = local_099.value()
        else:
            local_090 = self.record['090']
            if local_090 is not None and not self.entity_info.has_key('callno-lcc'): 
                self.entity_info['callno-lcc'] = local_090.value()


    def extract_udc(self):
        """
        Extracts Universal Decimal Classification Number
        """
        udc_values = self.__extract_callnumber__(['080',])
        if len(udc_values) > 0:
            self.entity_info['callno-udc'] = udc_values
         
 

class MARC21toPerson(MARC21Ingester):
    """
    MARC21toPerson ingests a MARC record into the BIBFRAME Redis datastore
    """

    def __init__(self, **kwargs):
        super(MARC21toPerson, self).__init__(**kwargs)
        self.person = None
        self.people = []
        self.field = kwargs.get("field", None)

    def __extract_identifier__(self,source_code,feature):
        """
        Helper function extracts all identifiers from 024 MARC21 fields,
        tests if source_code is equal $2 value and assigns to feature

        :param source_code: Source code to be tested
        :param feature: Name of the feature
        """
        output = []
        if self.record is None:
            return
        fields = self.record.get_fields('024')
        for field in fields:
            if field.indicator1 == '7':
                if field['2'] == source_code:
                    if field['a'] is not None:
                        output.append(field['a'])
                    for subfield in field.get_subfields('z'):
                        output.append(subfield)
                        self.redis_datastore.sadd("identifiers:{0}:invalid".format(feature)) 
        if len(output) > 0:
            if len(output) == 1:
                self.entity_info[feature] = output[0]
            else:
                self.entity_info[feature] = set(output)
    

    def extractDates(self):
        """
        Extracts rda:dateOfBirth and rda:dateOfDeath from MARC21 field
        """
        date_range = re.compile(r"(\d+)-*(\d*)")
        
        if self.field is not None and ['100','700','800'].count(self.field.tag)> -1:
            if ['0','1'].count(self.field.indicators[0]) > -1:
                raw_dates = ''.join(self.field.get_subfields('d'))
                if len(raw_dates) > 0:
                    date_result = date_range.search(raw_dates)
                    if date_result is not None:
                        groups = date_result.groups()
                        if len(groups[0]) > 0:
                            self.entity_info['rda:dateOfBirth'] = groups[0]
                        if len(groups[1]) > 0:
                            self.entity_info['rda:dateOfDeath'] = groups[1]
        if self.field.tag == '542':
            field542b = self.field.get_subfields('b')
            if len(field542b) > 0:
                self.entity_info['rda:dateOfDeath'] = ''.join(field542b)


    def extract_features(self):
        """
        Extracts features of the Person based on MARC21 fields
        """
        if self.field is not None and ['100','400','600','700','800'].count(self.field.tag) > -1:
            for name in self.field.get_subfields('a'):
                raw_names = [r.strip() for r in name.split(',')]
                if self.field.indicator1 == '0':
                    self.entity_info['schema:givenName'] = raw_names[0]
                elif self.field.indicator1 == '1':
                    self.entity_info['schema:familyName'] = raw_names.pop(0)
                    # Assigns the next raw_name to givenName 
                    for raw_name in raw_names:
                        tokens = raw_name.split(' ')
                        if len(tokens[0]) > 0:
                            if [".",",","/"].count(tokens[0][-1]) > 0:
                                tokens[0] = tokens[0][:-1]
                            self.entity_info['schema:givenName'] = tokens[0]
            for title in self.field.get_subfields('b'):
                 if self.entity_info.has_key('schema:honorificPrefix'):
                     if type(self.entity_info['schema:honorificPrefix']) == list:
                         self.entity_info['schema:honorificPrefix'].append(title)
                     else:
                         self.entity_info['schema:honorificPrefix'] = list(self.entity_info['schema:honorificPrefix'])
                 else:
                     self.entity_info['schema:honorificPrefix'] = title

    def extract_isni(self):
        """
        Extracts the ISNIInternational Standard Name Identifier
        """
        self.__extract_identifier__("isni","isni")
    
                            
    def extract_orcid(self):
        """
        Extracts the Open Researcher and Contributor Identifier
        """
        self.__extract_identifier__("orcid","orcid")


    def extract_preferredNameForThePerson(self):
        """
        Extracts RDA's preferredNameForThePerson from MARC21 record
        """
        preferred_name = []
        if self.field is not None and ['100','700','800'].count(self.field.tag)> -1:
            if ['0','1'].count(self.field.indicators[0]) > -1:
                preferred_name.extend(self.field.get_subfields('a','b'))
        if len(preferred_name) > 0:
            raw_name = ' '.join(preferred_name)
            if raw_name[-1] == ',':
                raw_name = raw_name[:-1]
            self.entity_info['rda:preferredNameForThePerson'] = raw_name  

    def extract_viaf(self):
        """
        Extracts the Virtual International Authority File number
        """
        self.__extract_identifier__("via,zf","viaf")


    def ingest(self):
        self.extract_features()
        self.extract_preferredNameForThePerson()
        self.extract_isni()
        self.extract_orcid()
        self.extract_viaf()
        self.extractDates()
        result = get_or_generate_person(self.entity_info,
                                        self.redis_datastore)
        if type(result) == list:
            self.people = result
        else:
            self.person = result
            self.people.append(self.person)


class MARC21toSubjects(MARC21Ingester):
    """
    MARC21toSubjects ingests a MARC21 record into the BIBFRAME Redis datastore
    """

    def __init__(self,**kwargs):
        """
        Creates a MARC21toSubject Ingester
        """
        super(MARC21toSubjects, self).__init__(**kwargs)
        self.creative_work = kwargs.get("work", None)
        self.field = kwargs.get("field", None)
        self.subjects = []

    def add_subdivision(self,subject_key):
        """
        Helper function iterates through the common 65x subdivision
        fields to create Authority Redis keys in the Redis datastore

        :param subject_key: Base subject key used to create subdivision
                            set keys for each subdivision
        """
        redis_pipeline = self.redis_datastore.pipeline()

        def add_subdivision(subfield, type_of):
            subdivision_key = "{0}:{1}".format(subfield[0],subfield[1])
            redis_pipeline.sadd("{0}:{1}".format(subject_key, type_of),
                subdivision_key)
            self.subjects.append(subdivision_key)
        for subfield in self.field.get_subfields('v'):
            add_subdivision(subfield, "form")
        for subfield in self.field.get_subfields('x'):
            add_subdivision(subfield, "general")
        for subfield in self.field.get_subfields('y'):
            add_subdivision(subfield, 'chronological')
        for subfield in self.field.get_subfields('z'):
            add_subdivision(subfield, 'geographic')
        redis_pipeline.execute()

    def extract_genre(self):
        """
        Extracts Genre from the MARC21 655 field
        """
        if self.field.tag == '651':
            subject_key = 'bf:Authority:Subject:Genre:{0}'.format(
                ''.join(self.field.get_subfields('a')))
            self.redis_datastore.sadd(subject_key,
                self.creative_work.redis_key)
            self.subjects.append(subject_key)

    def extract_geographic(self):
        """
        Extracts Geographic Subject from MARC21 651 field
        """
        if self.field.tag == '651':
            subject_key = 'bf:Authority:Subject:Geographic:{0}'.format(
                ''.join(self.field.get_subfields('a')))
            self.subjects.append(subject_key)
            self.add_subdivision(subject_key)

    def extract_topical(self):
        """
        Extracts Topical Subject from MARC21 650 field
        """
        if ['650'].count(self.field.tag) > -1:
            subject_key = 'bf:Authority:Subject:{0}'.format(
                ''.join(self.field.get_subfields('a')))
            self.subjects.append(subject_key)
            self.add_subdivision(subject_key)

    def ingest(self):
        self.extract_geographic()
        self.extract_genre()
        self.extract_topical()

class MARC21toCreativeWork(MARC21Ingester):
    "RLSP ingester takes a MARC21 record, creates/gets CreativeWork + children"

    def __init__(self, **kwargs):
        """Creates a MARC21toCreativeWork Ingester instance.

        Keywords:
        record -- MARC21 record
        """
        super(MARC21toCreativeWork, self).__init__(**kwargs)
        self.creative_work, self.work_class  = None, None

    def __classify_work_class__(self):
        "Classifies the work as specific Work class based on BIBFRAME website"
        leader = self.record.leader
        field007 = self.record['007']
        field336 = self.record['336']
        if leader[6] == 'a':
            if field007 is not None:
                test_value = field007.data[0]
                if test_value == 'a':
                    self.work_class = Map
                elif test_value == 'd':
                    self.work_class = Globe
                elif test_value == 'h': # Microfilm
                    self.work_class = StillImage
                elif test_value == 'q': # Notated music
                    self.work_class = NotatedMusic
                elif test_value == 'r':
                    self.work_class = RemoteSensingImage
                elif test_value == 's':
                    self.work_class = NonmusicalAudio
                elif ['m', 'v'].count(test_value) > 0:
                    self.work_class = MovingImage
            if self.work_class == None:
            # Book is the default for Language Material
                self.work_class = Book
        elif leader[6] == 'c':
            self.work_class = NotatedMusic
        elif leader[6] == 'd':
            self.work_class = Manuscript
        elif leader[6] == 'e' or leader[6] == 'f':
            # Cartography is the default
            self.work_class = Cartography
            if leader[6] == 'f':
                self.work_class = Manuscript
            if field007 is not None:
                if field007.data[0] == 'a':
                    self.work_class = Map
                elif field007.data[0] == 'd':
                    self.work_class = Globe
                elif field007.data[0] == 'r':
                    self.work_class = RemoteSensingImage
        elif leader[6] == 'g':
            self.work_class = MovingImage
        elif leader[6] == 'i':
            self.work_class = NonmusicalAudio
        elif leader[6] == 'j':
            self.work_class = MusicalAudio
        elif leader[6] == 'k':
            self.work_class = StillImage
        elif leader[6] == 'm':
            self.work_class = SoftwareOrMultimedia
        elif leader[6] == 'p':
            self.work_class = MixedMaterial
        elif leader[6] == 'r':
            self.work_class = ThreeDimensionalObject
        elif leader[6] == 't':
            self.work_class = Manuscript
        if self.work_class is None:
            self.work_class = Work

    def extract_creators(self):
        """
        Extracts and associates bf:Authority:Person entities creators
        work.
        """
        people_keys = []
        for field in self.record.get_fields('100','700','800'):
            if field is not None:
                people_ingester = MARC21toPerson(redis_datastore=self.redis_datastore,
                                                 field=field)
                people_ingester.ingest()
                for person in people_ingester.people:
                    people_keys.append(person.redis_key)
        for person_key in people_keys:
            if not self.entity_info.has_key('associatedAgent'):
                self.entity_info['associatedAgent'] = set()
            self.entity_info['associatedAgent'].add(person_key)
            if not self.entity_info.has_key('rda:isCreatedBy'):
                self.entity_info['rda:isCreatedBy'] = set()
            self.entity_info['rda:isCreatedBy'].add(person_key)
            

    def extract_note(self):
        """
        Extracts the note for the work
        """
        notes = []
        fields = self.record.get_fields('500')
        for field in fields:
            subfield3 = field['3']
            subfield_a = " ".join(field.get_subfields('a'))
            if subfield3 is not None:
                notes.append("{0} {1}".format(subfield3,
                                              subfield_a))
            else:
                notes.append(subfield_a)
        if len(notes) > 0:
            self.entity_info["note"] = set(notes)

    def extract_performerNote(self):
        "Extracts performerNote"
        notes = []
        fields = self.record.get_fields('511')
        for field in fields:
            notes.append("Cast: {0}".format(''.join(field.get_subfields('a'))))
        if len(notes) > 0:
            self.entity_info["performerNote"] = set(notes)

    def ingest(self):
        "Method ingests MARC Record into RLSP"
        self.__classify_work_class__()
        self.creative_work = self.work_class(
            redis_datastore=self.redis_datastore)
        work_titles = []
        for attribute, rules in self.creative_work.marc_map.iteritems():
            values = []
            #! NEED Title to check for duplicates
            if attribute == 'uniformTitle':
                pass
            if attribute == 'title':
                rule = rules[0]
                titleValue = ' '.join(self.__rule_one__(rule))
                title_entity = Title(redis_datastore=self.redis_datastore,
                                     titleValue=titleValue,
                                     label=self.record.title())
                title_entity.save()
                index_title(title_entity, self.redis_datastore)
                self.entity_info[attribute] = title_entity.redis_key
                work_titles.append(title_entity.redis_key)
                continue
            for rule in rules:
                result = list(set(self.__rule_one__(rule)))
                values.extend(result)
            if len(values) > 0:
                self.entity_info[attribute] = values
        # List of specific methods that haven't had Rule regex developed
        self.extract_creators()
        self.extract_note()
        self.extract_performerNote()
        self.get_or_add_work()
        if self.creative_work is not None:
            for title_key in work_titles: 
                self.redis_datastore.sadd(
                    "{0}:relatedResources".format(title_key),
                    self.creative_work.redis_key)
            
    def get_or_add_work(self,
                        classifer=simple_fuzzy.WorkClassifier):
        """Method returns a new Work or an existing work
         
        Default classifer does a similarity metric, basic similarity is 100% match
        (i.e. all fields must match or a new work is created)

        This method could use other Machine Learning techniques to improve
        the existing match with multiple and complex rule sets.

        Keywords
        classifier -- Classifer, default is the Simple Fuzzy Work Classifer 
        """
        # Assumes if 
        if self.entity_info.has_key('instanceOf'):
            self.entity_info['instanceOf'] = set(self.entity_info['instanceOf'])
        # If the title matches an existing Work's title and the creative work's creators, 
        # assumes that the Creative Work is the same.
        work_classifier = classifer(entity_info = self.entity_info,
                                    redis_datastore=self.redis_datastore,
                                    work_class=self.work_class)
        work_classifier.classify()
        self.creative_work = work_classifier.creative_work
        if self.creative_work is not None:
            self.creative_work.save()            
                
                
class MARC21toTitle(MARCParser):
    "Extracts BIBFRAME Title info from MARC21 record"

    def __init__(self, **kwargs):
        """Initializes MARC21toTitle object

        Parameters:
        """
        kwargs['rules_filename'] = 'bibframe-title-entity-map.json'
        super(MARC21toTitle, self).__init__(**kwargs)
        self.title_entity = None

    def __add_title_entity__(self):
        "Helper method adds a new Title"
        self.title_entity = Title(redis_datastore=self.redis_datastore)
        for key, value in self.entity_info.iteritems():
            if key is not None and value is not None:
                setattr(self.title_entity,
                        key,
                        value)
        self.title_entity.save()

    def __get_or_add_title_entity__(self):
        "Helper method returns new or existing Title"
        
        existing_titles = []
        if self.entity_info.get('titleValue') is not None:
            title_string = title
            if self.entity_info.get('subtitle') is not None:
                title_string += " {0}".format(
                    self.entity_info.get('subtitle'))
            self.entity_info['label'] = title_string

    def ingest(self):
        "Method finds or creates a Title in RLSP"
        self.parse()
        self.__add_title_entity__()

        

def check_marc_exists(instance_ds, record, marc_tag='907'):
    """
    Helper function checks to see the bib number is already associated with 
    a bibframe:Instance, returns True if that bibnumber already exists,
    False otherwise.

    :param instance_ds: BIBFRAME Instance 
    :param record: MARC21 record
    :param marc_tag: MARC tag of bib number, default to CC's III 907 
                     field   
    """
    field = record[marc_tag]
    if field is not None:
        raw_bib_id = ''.join(field.get_subfields('a'))
        # Extract III specific bib number
        bib_number = raw_bib_id[1:-1]
        if instance_ds.hexists('ils-bib-numbers', bib_number):
            return True
    return False
 

def ingest_marcfile(**kwargs):
    marc_filename = kwargs.get("marc_filename", None)
    redis_datastore = kwargs.get("redis_datastore",
                                 REDIS_DATASTORE)
    if IS_CONSORTIUM is not None and IS_CONSORTIUM is True:
        # Loads Prospector Consortium Libraries
        from themes.prospector.redis_helpers import load_prospector_orgs
        if not redis_datastore.exists('prospector-institution-codes'):
            load_prospector_orgs(redis_datastore)
    if marc_filename is not None:
        marc_file = open(marc_filename,'rb')
        count = 0
        marc_reader = pymarc.MARCReader(marc_file,
##                                        to_unicode=True,
                                        utf8_handling='ignore')
        start_time = datetime.datetime.now()
        sys.stderr.write("Starting at {0}\n".format(start_time.isoformat()))
        for record in marc_reader:
            # Need to check if MARC21 record has already been ingested into the
            # datastore
            if not check_marc_exists(redis_datastore, record):
                try:
                    ingester = MARC21toBIBFRAME(record=record,
                                                redis_datastore=redis_datastore)
                    ingester.ingest()
                except Exception as e:
                    print("Failed to ingest {0}={1}".format(
                        count,
                        e))
            if count%1000:
                if not count % 100:
                    sys.stderr.write(".")
            else:
                sys.stderr.write(str(count))

            count += 1
        end_time = datetime.datetime.now()
        sys.stderr.write("\nFinished at {0} count={1}\n".format(end_time.isoformat(),
                                                                count))
        sys.stderr.write("Total time elapsed is {0} seconds\n".format((end_time-start_time).seconds))

        return count

def info():
    print("Current working directory {0}".format(os.getcwd()))
