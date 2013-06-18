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
from bibframe.models import TitleEntity, ThreeDimensionalObject
from bibframe.ingesters.Ingester import Ingester
from call_number.redis_helpers import generate_call_number_app
from person_authority.redis_helpers import get_or_generate_person
from aristotle.settings import IS_CONSORTIUM, PROJECT_HOME
from title_search.redis_helpers import generate_title_app, process_title
from title_search.redis_helpers import index_title, search_title

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
        facet_key = "bf:Annotation:Facet:Access:{0}".format(access)
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
        # is either added to an existing set or creates a new
        # sorted set for the facet marcr:Annotation
        instance = kwargs.get("instance", self.instance)
        facet_key = "bf:Annotation:Facet:Format:{0}".format(
            getattr(instance,'rda:carrierTypeManifestation'))
        self.redis_datastore.sadd(facet_key, instance.redis_key)
        self.redis_datastore.zadd('bf:Annotation:Facet:Formats',
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
            facet_key = "bf:Annotation:Facet:LOCFirstLetter:{0}".format(
                lc_facet)
            self.redis_datastore.sadd(facet_key, creative_work.redis_key)
            self.redis_datastore.sadd("{0}:hasAnnotation".format(
                creative_work.redis_key),
                facet_key)
            self.redis_datastore.hset(
                "bf:Annotation:Facet:LOCFirstLetters",
                lc_facet,
                row)
            self.redis_datastore.zadd(
                "bf:Annotation:Facet:LOCFirstLetters:sort",
                float(self.redis_datastore.scard(facet_key)),
                facet_key)

    def add_language_facet(self, **kwargs):
        """
        Method takes an instance and adds to
        bibframe:Annotation:Facet:Language:LanguageTerm facet
        """
        pass

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
                redis_key = "bf:Annotation:Location:{0}".format(
                    output.get("site-code"))
                self.redis_datastore.sadd(redis_key, instance.redis_key)
                self.redis_datastore.hset(instance.redis_key,
                                      "ils-bib-number",
                                      output.get('ils-bib-number'))
                self.redis_datastore.hset(instance.redis_key,
                                      "ils-item-number",
                                      output.get('ils-item-number'))
                self.redis_datastore.zadd("bf:Annotation:Facet:Locations:sort",
                                        float(self.redis_datastore.scard(redis_key)),
                                        redis_key)
        else:
            locations = marc21_facets.get_cc_location(record)
            if len(locations) > 0:
                for location in locations:
                    redis_key = "bf:Annotation:Location:{0}".format(
                        location[0])
                    self.redis_datastore.sadd(redis_key, instance.redis_key)
                    if not self.redis_datastore.hexists(
                        "bibframe:Annotation:Facet:Locations",
                        location[0]):
                        self.redis_datastore.hset(
                            "bibframe:Annotation:Facet:Locations",
                            location[0],
                            location[1])
                    self.redis_datastore.zadd(
                        "bibframe:Annotation:Facet:Locations:sort",
                        float(self.redis_datastore.scard(redis_key)),
                        redis_key)
                    self.redis_datastore.sadd("{0}:hasAnnotation".format(instance.redis_key),
                                          redis_key)

    def add_publish_date_facet(instance, record):
        """
        Method adds the publication date of the instance to the
        bibframe:Annotation:Facet:PublishDate:{year}
        """
        pass

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
        #self.add_locations_facet(instance=instance,
        #    record=record)


isbn_regex = re.compile(r'([0-9\-]+)')


class MARC21toInstance(MARC21Ingester):
    """
    MARC21toInstance ingests a MARC record into the BIBFRAME Redis datastore
    """
    def __init__(self, **kwargs):
        self.instance = None
        super(MARC21toInstance, self).__init__(**kwargs)
        self.entity_info['rda:identifierForTheManifestation'] = {}


    def add_instance(self):
        """
        Method creates an marcr:Instance based on values for the entity
        """
        self.instance = Instance(redis_datastore=self.redis_datastore)
        for key,value in self.entity_info.iteritems():
            if key is not None and value is not None:
                setattr(self.instance,key,value)
        self.instance.save()

    def extract_024(self):
        """
        Extracts all 024 fields values and assigns to Instance
        """
        names = ['ansi',
                 'doi',
                 'ismn',
                 'iso',
                 'isrc',
                 'local',
                 'sici',
                 'upc',
                 'uri',
                 'urn']
        fields = self.record.get_fields('024')
        for field in fields:
            a_subfields = field.get_subfields('a')
            z_subfields = field.get_subfields('z')
            source_code = None
            if field.indicator1 == '0':
                source_code = 'isrc'
            if field.indicator1 == '1':
                source_code = 'upc'
            if field.indicator1 == '2':
                source_code = 'ismn'
            if field.indicator1 == '3':
                continue # Additional formating necessary for EAN
            if field.indicator1 == '4':
                source_code = 'sici'
            if field.indicator1 == '7':
                source_code = field['2']
            if not self.entity_info.has_key(source_code):
                self.entity_info[source_code] = []
            if source_code is not None:
                for subfield in a_subfields:
                    self.entity_info[source_code].append(subfield)
                for subfield in z_subfields:
                    self.entity_info[source_code].append(subfield)
                    self.redis_datastore.sadd('identifiers:{0}:invalid'.format(source_code),
                                          subfield)
        for name in names:
             if self.entity_info.has_key(name):
                 self.entity_info[name] = set(self.entity_info[name])             
                      

    def extract_028(self):
        """
        Extracts all 028 fields values and assigns to Instance  
        properties
        """
        fields = self.record.get_fields('028')
        names = {'0':'issue-number',
                 '1':'matrix-number',
                 '2':'music-plate',
                 '3':'music-publisher',
                 '4':'videorecording-identifier',
                 '5':'publisher-number'}
        for field in fields:
            a_subfield = field['a']
            if a_subfield is not None and names.has_key(field.indicator1):
                prop_name = names[field.indicator1]
                if self.entity_info.has_key(prop_name):
                    self.entity_info[prop_name].append(a_subfield)
                else:
                    self.entity_info[prop_name] = [a_subfield,]
        for name in names.values():
            if self.entity_info.has_key(name):
                self.entity_info[name] = set(self.entity_info[name])
            

    def extract_856(self):
        """
        Extracts all 856 fields values and assign to various Instance
        properties
        """
        fields = self.record.get_fields('856')
        for field in fields:
            u_subfields = field.get_subfields('u')
            if u_subfields is not None:
                for subfield in u_subfields:
                    for name in ['doi','hdl']:
                        if subfield.count(name) > 0:
                            if self.entity_info.has_key(name):
                                if type(self.entity_info[name]) is list:
                                    self.entity_info[name].append(subfield)
                                elif type(self.entity_info[name]) is set:
                                    self.entity_info[name].add(subfield)
                            else:
                                self.entity_info[name] = [subfield,]
        for name in ['doi','hdl']:
            if self.entity_info.has_key(name):
                self.entity_info[name] = set(self.entity_info[name])

    def extract_aspect_ratio(self):
        """
        Extracts Aspect Ratio from MARC21 record
        """
        output = []
        fields = self.record.get_fields('007')
        for field in fields:
            if field.data[0] == 'm':
                if field007_lkup['m']['4'].has_key(field.data[4]):
                    output.append(field007_lkup['m']['4'][field.data[4]])
        if len(output) > 0:
            self.entity_info['aspectRatio'] = set(output)


    def extract_award_note(self):
        """
        Extract's Award Note from MARC21 record
        """
        output = []
        fields = self.record.get_fields('586')
        for field in fields:
            note = ''
            if field['3'] is not None:
                note = '{0} '.format(field['3'])
            note += field['a']
            output.append(note)
        if len(output) > 0:
            self.entity_info['awardNote'] = set(output) 

    def extract_carrier_type(self):
        """
        Extract's the RDA carrier type from a MARC21 record and
        saves result as an Instance's rda:carrierTypeManifestation,

        NOTE: method currently using CC's MARC21 mapping, needs to
        normalized to the controlled vocabulary of rda:carrierType
        """
        self.entity_info['rda:carrierTypeManifestation'] = \
        marc21_facets.get_format(self.record)

    def extract_color_content(self):
        """
        Extract colorContent from MARC record
        """
        output = []
        fields = self.record.get_fields('007')
        for field in fields:
            type_of = field.data[0]
            if field007_lkup.has_key(type_of):
                if ["a","c","d","g","k","c","v"].count(type_of) > 0 and len(field.data) > 3:
                    if field007_lkup[type_of]["3"].has_key(field.data[3]):
                        output.append(field007_lkup[type_of]["3"][field.data[3]])
                elif type_of == "h":
                    if len(field.data) > 10:
                        if field007_lkup[type_of]["9"].has_key(field.data[9]):
                            output.append(field007_lkup[type_of]["9"][field.data[9]])
        if len(output) > 0:
            self.entity_info['colorContent'] = set(output) 

    def extract_coden(self):
        """
        Extracts CODEN from MARC record field 030, if the the field /z
        exists, adds value to set of invalid CODEN values
        """
        output = []
        all030s = self.record.get_fields('030')
        for field in all030s:
            for subfield in field.get_subfields('a'):
                output.append(subfield)
            for subfield in field.get_subfields('z'):
                output.append(subfield)
                self.redis_datastore.sadd('identifiers:CODEN:invalid',subfield)
        if len(output) > 0:
            self.entity_info['coden'] = set(output)


    def extract_duration(self):
        """
        Extracts duration 
        """
        output = []
        field = self.record['306']
        if field is not None:
            for subfield in field.get_subfields('a'):
                output.append(subfield)
        if len(output) > 0:
            self.entity_info['duration'] = set(output)

    def extract_ean(self):
        """
        Extracts International Article Identifier (EAN)
        """
        output = []
        fields = self.record.get_fields('024')
        for field in fields:
            if field.indicator1 == '3':
                a_subfield = field['a']
                z_subfield = field['z']
                d_subfield = field['d']
                ean = a_subfield
                if z_subfield is not None:
                    ean = '{0}-{1}'.format(ean,z_subfield)
                    self.redis_datastore.sadd('identifiers:ean:invalid',
                                          z_subfield)
                if d_subfield is not None:
                    ean = '{0}-{1}'.format(ean,d_subfield)
                output.append(ean)
        if len(output) > 0:
            self.entity_info['ean'] = set(output)

    def extract_fingerprint(self):
        """
        Extract's unparsed fingerprint
        """
        output = []
        fields = self.record.get_fields('026')
        for field in fields:
            subfield_e = field['e']
            if subfield_e is not None:
                output.append(subfield_e)
        if len(output) > 0:
            self.entity_info['fingerprint'] = set(output)

    def extract_illustrative_content_note(self):
        """
        Extract Illustrative Content Note
        """
        output = []
        # Need to check 008
        fields = self.record.get_fields('300')
        for field in fields:
            if field['b'] is not None:
                output.append(field['b'])
        if len(output) > 0:
            self.entity_info['illustrativeContentNote'] = set(output)

    def extract_ils_bibnumber(self):
        """
        Extract's ILS bibliographic number from MARC21 record and
        saves as a rda:identifierForTheManifestation
        """
        field907 = self.record['907']
        if field907 is not None:
            raw_bib_id = ''.join(field907.get_subfields('a'))
            # Extract III specific bib number
            bib_number = raw_bib_id[1:-1]
            self.entity_info['rda:identifierForTheManifestation']['ils-bib-number'] = bib_number

    def extract_intended_audience(self):
        """
        Exracts Intended Audience
        """
        output = []
        field521_lkup = {
            "0": "Reading grade level", 
            "1": "Interest age level", 
            "2": "Interest grade level", 
            "3": "Special audience characteristics", 
            "4": "Motivation/interest level", 
            "8": "No display constant generated"}
        #! Need to Process 008
        fields = self.record.get_fields('521')
        for field in fields:
            prefix = field521_lkup.get(field.indicator1,None)
            for subfield in field.get_subfields('a'):
                if prefix is not None:
                    output.append("{0} {1}".format(prefix,subfield))
                else:
                    output.append(subfield)
        if len(output) > 0:
            self.entity_info['intendedAudience'] = set(output)
                                                    
            


    def extract_isbn(self):
        """
        Extract's ISBN  from MARC21 record and
        saves as a rda:identifierForTheManifestation:isbn
        """
        isbn_fields = self.record.get_fields('020')
        isbn_values = []
        for isbn_field in isbn_fields:
            for subfield in isbn_field.get_subfields('a'):
                isbn_values.append(subfield)
            for subfield in isbn_field.get_subfields('z'):
                isbn_values.append(subfield)
                self.redis_datastore.sadd("identifiers:isbn:invalid",subfield)
        if len(isbn_values) > 0:
            self.entity_info['isbn'] = set(isbn_values)

    def extract_issn(self):
        """
        Extract's ISSN  from MARC21 record and
        saves as a rda:identifierForTheManifestation:issn
        """
        issn_fields= self.record.get_fields('022')
        issn_values = []
        for field in issn_fields:
            for subfield in field.get_subfields('a','y'):
                issn_values.append(subfield)
            for subfield in field.get_subfields('z'):
                issn_values.append(subfield)
                self.redis_datastore.sadd("identifiers:issn:invalid",subfield)
        if len(issn_values) > 0:
            self.entity_info['issn'] = set(issn_values)

    def extract_language(self):
        """
        Extract language
        """
        output = []
        fields = self.record.get_fields('008')
        for field in fields:
            if field.tag == '008':
                output.append(field.data[35:38])
        if len(output) > 0:
            self.entity_info['language'] = set(output)

    def extract_lccn(self):
        """
        Extract's LCCN from MARC21 record
        """
        lccn_field = self.record['010']
        if lccn_field is not None:
            subfield_a = lccn_field['a']
            subfield_z = lccn_field['z']
            if subfield_a is not None and subfield_z is not None:
                self.entity_info['lccn'] = set([subfield_a, subfield_z])
            elif subfield_a is not None and subfield_z is None:
                self.entity_info['lccn'] = subfield_a
            elif subfield_a is None and subfield_z is not None:
                self.entity_info['lccn'] = subfield_z
            if subfield_z is not None:
                self.redis_datastore.sadd('identifiers:lccn:invalid',subfield_z)


    def extract_lc_overseas_acq(self):
        """
        Extract's Library of Congress Overseas Acquisition Program number
        """
        output = []
        all025s = self.record.get_fields('025')
        for field in all025s:
            output.append(field['a'])
        if len(output) > 0:
            self.entity_info['lc-overseas-acq'] = set(output)

    def extract_legal_deposit(self):
        """
        copyright or legal deposit number
        """
        output = []
        fields = self.record.get_fields('017')
        for field in fields:
            a_subfields = field.get_subfields('a')
            z_subfields = field.get_subfields('z')
            for subfield in a_subfields:
                output.append(subfield)
            for subfield in z_subfields:
                output.append(subfield)
                self.redis_datastore.sadd("identifiers:legal-deposit:invalid",subfield)
        if len(output) > 0:
           self.entity_info['legal-deposit'] = set(output)

    def extract_date_of_publication(self):
        """
        Extracts the date of publication and saves as a
        rda:dateOfPublicationManifestation
        """
        field008 = self.record['008']
        pub_date = None
        pub_date = field008.data[7:11]
        # Need to check for the following fields if pub_date is absent
        # 008[1:15], 260c, 542i
        self.entity_info['rda:dateOfPublicationManifestation'] = pub_date


    def extract_medium_of_music(self):
        """
        Extracts mediumOfMusic
        """
        output = []
        fields = self.record.get_fields('382')
        for field in fields:
            for subfield in field.get_subfields('a'):
                output.append(subfield)
        if len(output) > 0:
            self.entity_info['mediumOfMusic'] = set(output)

    def extract_nban(self):
        """
        Extracts National bibliography agency control number
        """
        output = []
        fields = self.record.get_fields('016')
        for field in fields:
            subfields = field.get_subfields('a')
            for subfield in subfields:
                output.append(subfield)
            subfields = field.get_subfields('z')
            for subfield in subfields:
                output.append(subfield)
                self.redis_datastore.sadd('identifiers:nban:invalid',subfield)
        if len(output) > 0:
            self.entity_info['nban'] = set(output)


    def extract_nbn(self):
        """
        Extracts the National Bibliography Number
        """
        output = []
        fields = self.record.get_fields('015')
        for field in fields:
            for subfield in field.get_subfields('a'):
                output.append(subfield)
            for subfield in field.get_subfields('z'):
                output.append(subfield)
                self.redis_datastore.sadd("identifers:nbn:invalid",subfield)
        if len(output) > 0:
            self.entity_info['nbn'] = set(output)
 

    def extract_organization_system(self):
        """
        Extracts Organization System
        """
        output = []
        fields = self.record.get_fields("351")
        for field in fields:
            org_system = ''
            subfield3 = field["3"]
            subfieldc = field["c"]
            a_subfields = field.get_subfields('a')
            b_subfields = field.get_subfields('b')
            if subfield3 is not None:
                org_system = "{0}".format(subfield3)
            for subfield_a in a_subfields:
                org = "{0} {1}".format(org_system,subfield_a)
                for subfield_b in b_subfields:
                    arrang = "{0} {1}".format(org,subfield_b)
                    if subfieldc is not None:
                        output.append("{0}={1}".format(arrang,subfieldc))
                    else:
                        output.append(arrang)
            if len(b_subfields) > 0 and len(a_subfields) < 1:
                for subfield_b in b_subfields:
                    arrang = "{0} {1}".format(org_system,subfield_b)
                    if subfieldc is not None:
                        output.append("{0}={1}".format(arrang,subfieldc))
                    else:
                        output.append(arrang)
            if len(output) > 0:
                self.entity_info['organizationSystem'] = set(output)
 

    def extract_performers_note(self):
        """
        Extracts Performers Note
        """
        output = []
        fields = self.record.get_fields('511')
        for field in fields:
            subfields = field.get_subfields('a')
            for subfield in subfields:
                output.append('Cast: {0}'.format(subfield))
        if len(output) > 0:
            self.entity_info['performerNote'] = set(output)

    def extract_report_number(self):
        """
        Extracts report-number 
        """ 
        output = []
        fields = self.record.get_fields('088')
        for field in fields:
            subfields = field.get_subfields('a')
            for subfield in subfields:
                output.append(subfield)
            invalid_subfields = field.get_subfields('z')
            for subfield in invalid_subfields:
                output.append(subfield)
                self.redis_datastore.sadd("identifiers:report-number:invalid",
                                      subfield)
        if len(output) > 0:
            self.entity_info['report-number'] = set(output)

    def extract_sound_content(self):
        """
        Extract sound content 
        """
        output = []
        fields = self.record.get_fields('007')
        for field in fields:
            type_of = field.data[0]
            if field007_lkup.has_key(type_of):
                if len(field.data) < 7:
                    continue
                code5 = field.data[5].strip()
                if len(code5) < 1:
                    code5 = None
                code6 = field.data[6].strip()
                if len(code6) < 1:
                    code6 = None
                if type_of == "c":
                    if field007_lkup[type_of]["5"].has_key(code5): 
                        output.append(field007_lkup[type_of]["5"][code5])
                elif ["g","m","v"].count(type_of) > 0:
                    if field007_lkup[type_of]["5"].has_key(code5):
                         output.append(field007_lkup[type_of]["5"][code5])
                    if field007_lkup[type_of]["6"].has_key(code6):
                         output.append(field007_lkup[type_of]["6"][code6])
        if len(output) > 0:
             self.entity_info['soundContent'] = set(output)
         
    def extract_strn(self):
        """
        Extract Standard Technical Report Number
        """
        output = []
        fields = self.record.get_fields('027')
        for field in fields:
            for subfield in field.get_subfields('a'):
                output.append(subfield)
            for subfield in field.get_subfields('z'):
                output.append(subfield)
                self.redis_datastore.sadd("identifiers:strn:invalid",subfield)
        if len(output) > 0:
            self.entity_info['strn'] = set(output)


    def extract_supplementaryContentNote(self):
        """
        Extract Supplementary content note
        """
        output = []
        fields = self.record.get_fields('504','525')
        for field in fields:
            if field.tag == '504':
                note = field['a']
                if field['b'] is not None:
                    note = '{0} References: {1}'.format(note,
                                                        field['b'])
                output.append(note)
            elif field.tag == '525':
                output.append(field['a'])
        if len(output) > 0:
            self.entity_info['supplementaryContentNote'] = set(output)
                   

    def extract_stock_number(self):
        """
        Extracts stock number for the acquisition 
        """
        output = []
        all037s = self.record.get_fields('037')
        for field in all037s:
            output.append(field['a'])
        if len(output) > 0:
            self.entity_info['stock-number'] = set(output)


    def extract_study_number(self):
        """
        Extracts study number
        """
        field036 = self.record['036']
        if field036 is not None:
            if field036['a'] is not None:
                self.entity_info['study-number'] = field036['a']



    def extract_sudoc(self):
        """
        Extracts sudoc call-number from MARC record and
        saves as a rda:identifierForTheManifestation
        """
        sudoc_field = self.record['086']
        if sudoc_field is not None:
            self.entity_info['rda:identifierForTheManifestation']['sudoc'] = sudoc_field.value()

    def extract_system_number(self):
        """
        Extracts system control number
        """
        output = []
        fields = self.record.get_fields('035')
        for field in fields:
            for subfield in field.get_subfields('a'):
                output.append(subfield)
            for subfield in field.get_subfields('z'):
                output.append(subfield)
                self.redis_datastore.sadd("identifiers:system-number:invalid",subfield)
        if len(output) > 0:
            self.entity_info['system-number'] = set(output)

    def extract_url(self):
        """
        Extracts Uniform resource locator 
        """
        output = []
        fields = self.record.get_fields('856')
        for field in fields:
            for subfield in field.get_subfields('u'):
                output.append(subfield)
        if len(output) > 0:
            self.entity_info['rda:uniformResourceLocatorItem'] = set(output) 

    def ingest(self):
        """
        Ingests a MARC21 record into a BIBFRAME Instance Redis datastore
        """
        self.extract_024()
        self.extract_028()
        self.extract_856()
        self.extract_aspect_ratio()
        self.extract_award_note()
        self.extract_carrier_type()
        self.extract_color_content()
        self.extract_coden()
        self.extract_duration()
        self.extract_illustrative_content_note()
        self.extract_intended_audience()
        self.extract_ean()
        self.extract_fingerprint()
        self.extract_sound_content()
        self.extract_ils_bibnumber()
        self.extract_isbn()
        self.extract_issn()
        #self.extract_issnl()
        self.extract_language()
        self.extract_lc_overseas_acq()
        self.extract_lccn()
        self.extract_legal_deposit()
        self.extract_medium_of_music()
        self.extract_nban()
        self.extract_nbn()
        self.extract_organization_system()
        self.extract_performers_note()
        self.extract_report_number()
        self.extract_stock_number()
        self.extract_strn()
        self.extract_study_number()
        self.extract_sudoc()
        self.extract_supplementaryContentNote()
        self.extract_system_number()
        self.extract_date_of_publication()
        self.extract_url()
        self.add_instance()
        

class MARC21toBIBFRAME(MARC21Ingester):
    """
    MARC21toBIBFRAME takes a MARC21 record and ingests into BIBFRAME Redis
    datastore
    """

    def __init__(self, **kwargs):
        super(MARC21toBIBFRAME, self).__init__(**kwargs)
        

    def ingest(self):
        "Method runs a complete ingestion of a MARC21 record into RLSP"
        # Start with either a new or existing Creative Work or subclass
        # like Book, Article, MusicalAudio, or MovingImage
        self.marc2creative_work = MARC21toCreativeWork(
            redis_datastore=self.redis_datastore,
            record=self.record)
        self.marc2creative_work.ingest()
        # Exit ingest if a creative work is missing
        if self.marc2creative_work.creative_work is None:
            return
        work_key = self.marc2creative_work.creative_work.redis_key
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
        self.marc2library_holdings = MARC21toLibraryHolding(
            redis_datastore=self.redis_datastore,
            record=self.record,
            instance=self.marc2instance.instance)
        self.marc2library_holdings.ingest()
        if self.redis_datastore.hexists(self.marc2instance.instance.redis_key,
                                    'hasAnnotation'):
            annotation = self.marc2instance.instance.hasAnnotation
            self.redis_datastore.hdel(self.marc2instance.instance.redis_key,
                                  'hasAnnotation')
            self.redis_datastore.sadd("{0}:hasAnnotation".format(self.marc2instance.instance.redis_key),
                                  annotation)
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
        self.instance = kwargs.get('instance', None)

    def __add_cc_holdings__(self):
        "Helper function for Colorado College MARC Records"
        # Assumes hybrid environment
        cc_key = self.redis_datastore.hget('prospector-institution-codes',
                                           '9cocp')
        holding = Holding(redis_datastore=self.redis_datastore)
        for key, value in self.entity_info.iteritems():
            setattr(holding, key, value)
        setattr(holding, 'schema:contentLocation', cc_key)
        holding.save()
        self.redis_datastore.sadd("{0}:resourceRole:own".format(cc_key),
                                  holding.redis_key)
        if hasattr(holding, 'ils-bib-number'):
            self.redis_datastore.hadd('ils-bib-numbers',
                                      getattr(holding, 'ils-bib-number'),
                                      holding.redis_key)
        self.holdings.append(holding)
        
        

    def __add_consortium_holdings__(self):
        "Helper function for CARL Alliance MARC records"
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
                holding.save()
                self.redis_datastore.hadd(
                    'ils-bib-numbers',
                    getattr(holding, 'ils-bib-number'),
                    holding.redis_key)
                if self.instance is not None:
                    instance_annotation_key = "{0}:hasAnnotation".format(
                        self.instance.redis_key)
                    self.redis_datastore.sadd(instance_annotation_key,
                                          holding.redis_key)
                    self.redis_datastore.sadd("{0}:keys".format(self.instance.redis_key),
                                          instance_annotation_key)
                # Use MARC Relator Code for set key 
                self.redis_datastore.sadd("{0}:resourceRole:own".format(org_key),
                                          holding.redis_key)
                self.holdings.append(holding)


    def add_holdings(self):
        """
        Creates one or more Library Holdings based on values in the entity
        """
        
        if settings.IS_CONSORTIUM is True:
            self.__add_consortium_holdings__()
        else:
            # CC specific III MARC record format, should be modified to be more
            # generic
            self.__add_cc_holdings__()
 

    
            


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
            #! NEED TitleEntity to check for duplicates
            if attribute == 'uniformTitle':
                pass
            if attribute == 'title':
                rule = rules[0]
                titleValue = ' '.join(self.__rule_one__(rule))
                title_entity = TitleEntity(redis_datastore=self.redis_datastore,
                                           titleValue=titleValue,
                                           label=self.record.title())
                title_entity.save()
                index_title(title_entity, self.redis_datastore)
                self.entity_info[attribute] = title_entity.redis_key
                work_titles.append(title_entity.redis_key)
                continue
            for rule in rules:
                result = list(set(self.__rule_one__(rule))
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
                
                
class MARC21toTitleEntity(MARC21Ingester):
    "Extracts BIBFRAME TitleEntity info from MARC21 record"

    def __init__(self, **kwargs):
        """Initializes MARC21toTitleEntity object

        Parameters:
        """
        super(MARC21toTitleEntity, self).__init__(**kwargs)
        self.title_entity = None

    def __get_or_add_title_entity__(self):
        "Helper method returns new or existing TitleEntity"
        existing_titles = []
        if self.entity_info.get('titleValue') is not None:
            title_string = title
            if self.entity_info.get('subtitle') is not None:
                title_string += " {0}".format(
                    self.entity_info.get('subtitle'))
            self.entity_info['label'] = title_string
            
                
                                    

    def ingest(self):
        "Method finds or creates a TitleEntity in RLSP"
        for attribute, rules in TitleEntity.marc_map.iteritems():
            values = []
            for rule in rules:
                values.extend(self.__rule_one__(rule))
            if len(values) > 0:
                self.entity_info[attribute] = values
        
            
        


##
##    def extract_classification(self):
##        """
##        Extracts classification from MARC
##        """
##        class_vals = []
##        fields = self.record.get_fields('084','086')
##        for field in fields:
##            if field.tag == '084':
##                class_vals.append(field.value())
##            if field.tag == '086':
##                class_vals.append(field['a'])
##        if len(class_vals) > 1:
##            self.entity_info['classification'] = set(class_vals)
##        elif len(class_vals) == 1:
##            self.entity_info['classification'] = class_vals[0]
##
##    def extract_class_ddc(self):
##        """
##        Extracts Dewey Decimal Classification from MARC record
##        """
##        ddc_vals = []
##        fields = self.record.get_fields('082','083')
##        for field in fields:
##            if field.tag == '083':
##                ddc_vals.append('-'.join(field.get_subfields('a','c')))
##            if field.tag == '082':
##                ddc_vals.append(''.join(field.get_subfields('a')))
##        if len(ddc_vals) > 0:
##            self.entity_info['class-ddc'] = set(ddc_vals)
##
##    def extract_class_lcc(self):
##        """
##        Extracts Library of Congress Classification from MARC record
##        """
##        lcc_vals = []
##        fields = self.record.get_fields('050','051','055','060','061','070','071')
##        for field in fields:
##            if field['a'] is not None:
##                lcc_vals.append(field['a'])
##        if len(lcc_vals) > 0:
##            self.entity_info['class-lcc'] = set(lcc_vals)
##
##    def extract_class_udc(self):
##        """
##        Extracts Universal Decimal Classification Number
##        """
##        udc_values = []
##        fields = self.record.get_fields('080')
##        for field in fields:
##            udc_values.append(field.value())
##        if len(udc_values) > 0:
##            self.entity_info['class-udc'] = set(udc_values)
##
##    def extract_contentCoverage(self):
##        """
##        Extracts Nature of Content
##        """
##        coverages = []
##        fields = self.record.get_fields('518','513','522')
##        for field in fields:
##            if field.tag == '518':
##                if field['a'] is not None:
##                    coverages.append(field['a'])
##            if field.tag == '513':
##                if field['b'] is not None:
##                    coverages.append(field['b'])
##            if field.tag == '522':
##                if field['a'] is not None:
##                    coverages.append(field['a'])
##        if len(fields) > 0:
##            self.entity_info['contentCoverage'] = set(fields)
##
##
##
##    def extract_contentNature(self):
##        """
##        Extracts Nature of Content
##        """
##        content_natures = []
##        fields = self.record.get_fields('245','513','008','336')
##        for field in fields:
##            if field.tag == '245':
##                if field['k'] is not None:
##                    content_natures.append(field['k'])
##            if field.tag == '513':
##                if field['a'] is not None:
##                    content_natures.append(field['a'])
##            if field.tag == '008':
##                pass #! TODO need a look-up on 008 BK and CR
##            if field.tag == '336':
##                if field['a'] is not None:
##                    content_natures.append("{0}(term)".format(field['a']))
##                if field['b'] is not None:
##                    content_natures.append("{0}(code)".format(field['b']))
##        if len(content_natures) > 0:
##            self.entity_info['contentNature'] = set(content_natures)
##                                            
##            
##
##        
##    def extract_creditNotes(self):
##        """
##        Extracts creditNotes from MARC
##        """
##        credit_notes = []
##        fields = self.record.get_fields('508')
##        for field in fields:
##            credit_notes.append("Credits: {0}".format(field['a']))
##        if len(credit_notes) > 0:
##            self.entity_info['creditNote'] = set(credit_notes)
##
##    def extract_creators(self):
##        """
##        Extracts and associates bf:Authority:Person entities creators
##        work.
##        """
##        people_keys = []
##        for field in self.record.get_fields('100','700','800'):
##            if field is not None:
##                people_ingester = MARC21toPerson(redis_datastore=self.redis_datastore,
##                                                 field=field)
##                people_ingester.ingest()
##                for person in people_ingester.people:
##                    people_keys.append(person.redis_key)
##        for person_key in people_keys:
##            if not self.entity_info.has_key('associatedAgent'):
##                self.entity_info['associatedAgent'] = set()
##            self.entity_info['associatedAgent'].add(person_key)
##            if not self.entity_info.has_key('rda:isCreatedBy'):
##                self.entity_info['rda:isCreatedBy'] = set()
##            self.entity_info['rda:isCreatedBy'].add(person_key)
##
##    def __extract_other_std_id__(self,
##                                 tag,
##                                 source_code):
##        """
##        Helper function for isan, istc and other standard fields 
##
##        :param tag: Required MARC field number
##        :param indicator1: Value of indicator, defaults to 7
##        """
##        output = []
##        fields = self.record.get_fields(tag)
##        for field in fields:    
##            if field.indicator1 == '7':
##                extracted_code = field['2']
##                if extracted_code == source_code:
##                    for subfield in field.get_subfields('a','z'):
##                        output.append(subfield)
##        return output
##                                      
##    def extract_intendedAudience(self):
##        """
##        Extracts intendedAudience
##        """
##        audiences = []
##        fields = self.record.get_fields('008','521')
##        for field in fields:
##            if field.tag == '008':
##                pass #! TODO extract type and do look up for value
##            if field.tag == '521':
##                subfield_a_lst = field.get_subfields('a')
##                for subfield in subfield_a_lst:
##                    if field.indicator1 == '0':
##                        audiences.append("Reading grade level {0}".format(subfield))
##                    elif field.indicator1 == '1':
##                        audiences.append("Interest age level {0}".format(subfield))
##                    elif field.indicator1 == '2':
##                        audiences.append("Interest grade level {0}".format(subfield))
##                    elif field.indicator1 == '3':
##                        audiences.append("Special audiences {0}".format(subfield))
##                    elif field.indicator1 == '4':
##                        audiences.append("Motivation/interest level {0}".format(subfield))
##        if len(audiences) > 0:
##            self.entity_info['intendedAudience'] = set(audiences)
##                    
##                
##
##    def extract_isan(self):
##        """
##        Extracts International Standard Audiovisual Number (isan)
##        """
##        isan_vals = self.__extract_other_std_id__('024','isan')
##        if len(isan_vals) > 1:
##            self.entity_info["isan"] = set(isan_vals)
##        elif len(isan_vals) == 1:
##            self.entity_info["isan"] = isan_vals[0]
##        
##
##    def extract_istc(self):
##        """
##        Extracts International Standard Text code (istc)
##        """
##        isan_vals = self.__extract_other_std_id__('024','istc')
##        if len(isan_vals) > 1:
##            self.entity_info["istc"] = set(isan_vals)
##        elif len(isan_vals) == 1:
##            self.entity_info["istc"] = isan_vals[0]
##
##    def extract_iswc(self):
##        """
##        Extracts International Standard Mustic Work Code (iswc)
##        """
##        isan_vals = self.__extract_other_std_id__('024','iswc')
##        if len(isan_vals) > 1:
##            self.entity_info["iswc"] = set(isan_vals)
##        elif len(isan_vals) == 1:
##            self.entity_info["iswc"] = isan_vals[0]
##    
##    def extract_issnl(self):
##        """
##        Extracts linking International Standard Serial Number
##        """
##        issnl_nums = []
##        fields = self.record.get_fields('022')
##        for field in fields:
##            for subfield in field.get_subfields('1','m'):
##                issnl_nums.append(subfield)
##        if len(issnl_nums) > 0:
##            self.entity_info["issn-l"] = set(issnl_nums)
##                                           
##    def extract_note(self):
##        """
##        Extracts the note for the work
##        """
##        notes = []
##        fields = self.record.get_fields('500')
##        for field in fields:
##            subfield3 = field['3']
##            if subfield3 is not None:
##                notes.append("{0} {1}".format(subfield3,
##                                              ''.join(field.get_subfields('a'))))
##        if len(notes) > 0:
##            self.entity_info["note"] = set(notes)
##            
##    def extract_performerNote(self):
##        """
##        Extracts performerNote
##        """
##        notes = []
##        fields = self.record.get_fields('511')
##        for field in fields:
##            notes.append("Cast: {0}".format(''.join(field.get_subfields('a'))))
##        if len(notes) > 0:
##            self.entity_info["performerNote"] = set(notes)
##
##    def extract_subjects(self):
##        """
##        Extracts amd associates bf:Authority:rda:Subjects entities
##        with the creators work.
##        """
##        subject_keys = []
##
##
##    def extract_title(self):
##        """
##        Extracts rda:titleProper from MARC21 record
##        """
##        slash_re = re.compile(r"/$")
##        title_field = self.record['245']
##        if title_field is not None:
##            raw_title = ''.join(title_field.get_subfields('a'))
##            if slash_re.search(raw_title):
##                raw_title = slash_re.sub("",raw_title).strip()
##            subfield_b = ' '.join(title_field.get_subfields('b'))
##            if slash_re.search(subfield_b):
##                subfield_b = slash_re.sub("",subfield_b).strip()
##            raw_title += ' {0}'.format(subfield_b)
##            if raw_title.startswith("..."):
##                raw_title = raw_title.replace("...","")
##            self.entity_info['title'] = {'rda:title':raw_title,
##			'sort':raw_title.lower()}
##            indicator_one = title_field.indicators[1]
##            try:
##                indicator_one = int(indicator_one)
##            except ValueError:
##                indicator_one = 0
##            if int(indicator_one) > 0:
##                self.entity_info['variantTitle'] = raw_title[indicator_one:]
##                self.entity_info['title']['sort'] = self.entity_info['variantTitle']
##
##              
##
##    def get_or_add_work(self,
##                        classifer=simple_fuzzy.WorkClassifier):
##        """
##        Method either returns a new Work or an existing work based
##        on a similarity metric, basic similarity is 100% match
##        (i.e. all fields must match or a new work is created)
##
##        This method could use other Machine Learning techniques to improve
##        the existing match with mutliple and complex rule sets. 
##        """
##        if self.entity_info.has_key('bibframe:Instances'):
##            self.entity_info['bibframe:Instances'] = set(self.entity_info['bibframe:Instances'])
##        # If the title matches an existing Work's title and the creative work's creators, 
##        # assumes that the Creative Work is the same.
##        work_classifier = classifer(redis_datastore = self.redis_datastore,
##                                    authority_ds = self.redis_datastore,
##                                    creative_work_ds = self.redis_datastore,
##                                    instance_ds = self.redis_datastore,
##                                    entity_info = self.entity_info)
##        work_classifier.classify()
##        self.creative_work = work_classifier.creative_work
##        if self.creative_work is not None:
##            self.creative_work.save()
##
##    def ingest(self):
##        """
##        Method ingests a MARC21 record into the BIBFRAME datastore
##
##        :param record: MARC21 record
##        """
##        self.extract_classification()
##        self.extract_class_ddc()
##        self.extract_class_lcc()
##        self.extract_class_udc()
##        self.extract_contentCoverage()
##        self.extract_contentNature()
##        self.extract_creditNotes()
##        self.extract_intendedAudience()
##        self.extract_isan()
##        self.extract_istc()
##        self.extract_iswc()
##        self.extract_issnl()
##        self.extract_title()
##        self.extract_creators()
##        self.extract_note()
##        self.extract_performerNote()
##        self.get_or_add_work()
##        # Adds work to creators
##        if self.creative_work is not None:
##            if self.creative_work.associatedAgent is not None:
##                for creator_key in list(self.creative_work.associatedAgent):
##                    creator_set_key = "{0}:rda:isCreatorPersonOf".format(creator_key)
##                    self.redis_datastore.sadd(creator_set_key,
##                                           self.creative_work.redis_key)
##            self.creative_work.save()
##            generate_title_app(self.creative_work,self.redis_datastore)
##        super(MARC21toCreativeWork, self).ingest()



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
    print("IN ingest_marcfile {0} to {1}".format(redis_datastore,
                                                 marc_filename))
    if IS_CONSORTIUM is not None:
        # Loads Prospector Consortium Libraries
        from themes.prospector.redis_helpers import load_prospector_orgs
        load_prospector_orgs(redis_datastore)
    if marc_filename is not None:
        marc_file = open(marc_filename,'rb')
        count = 0
        marc_reader = pymarc.MARCReader(marc_file,
                                        utf8_handling='ignore')
        start_time = datetime.datetime.now()
        sys.stderr.write("Starting at {0}\n".format(start_time.isoformat()))
        for record in marc_reader:
            # Need to check if MARC21 record has already been ingested into the
            # datastore
            if not check_marc_exists(redis_datastore, record):
                ingester = MARC21toBIBFRAME(record=record,
                                            redis_datastore=redis_datastore)
                ingester.ingest()
            if count%1000:
                if not count % 100:
                    sys.stderr.write(".")
            else:
                sys.stderr.write(str(count))

            count += 1
        end_time = datetime.datetime.now()
        sys.stderr.write("\nFinished at {0}\n".format(end_time.isoformat()))
        sys.stderr.write("Total time elapsed is {0} seconds\n".format((end_time-start_time).seconds))

        return count

def info():
    print("Current working directory {0}".format(os.getcwd()))
