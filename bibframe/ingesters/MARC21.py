"""
 :mod:`ingesters` Module ingests MARC21 and MODS records into a MARCR-Redis datastore
 controlled by the MARCR app.
"""
__author__ = "Jeremy Nelson"

import datetime, re, pymarc, os, sys,logging, redis, time
from bibframe.models import Annotation, Organization, Work, Holding, Instance, Person
from bibframe.ingesters.Ingester import Ingester
from call_number.redis_helpers import generate_call_number_app
from person_authority.redis_helpers import get_or_generate_person
from aristotle.settings import PROJECT_HOME
from title_search.redis_helpers import generate_title_app,search_title
import marc21_facets
from lxml import etree
from rdflib import RDF,RDFS,Namespace
import json

try:
    import aristotle.settings as settings
    CREATIVE_WORK_REDIS = settings.CREATIVE_WORK_REDIS
    INSTANCE_REDIS = settings.INSTANCE_REDIS
    AUTHORITY_REDIS = settings.AUTHORITY_REDIS
    ANNOTATION_REDIS = settings.ANNOTATION_REDIS
    OPERATIONAL_REDIS = settings.OPERATIONAL_REDIS
except ImportError, e:
    redis_host = '0.0.0.0'
    CREATIVE_WORK_REDIS = redis.StrictRedis(port=6380)
    INSTANCE_REDIS = redis.StrictRedis(port=6381)
    AUTHORITY_REDIS = redis.StrictRedis(port=6382)
    ANNOTATION_REDIS = redis.StrictRedis(port=6383)
    OPERATIONAL_REDIS = redis.StrictRedis(port=6379)


field007_lkup = json.load(open(os.path.join(PROJECT_HOME,
                                            "bibframe",
                                            "fixures",
                                            "marc21-007.json"),

                                "rb"))


MARC_FLD_RE = re.compile(r"(\d+)([-|w+])([-|w+])/(\w+)")
class MARC21Helpers(object):
    """
    MARC21 Helpers for MARC21 Ingester classes
    """
    marc_fld_re = re.compile(r"(\d+)(--)*([//].+)*[,]*")

    def __init__(self,marc_record):
        self.record = marc_record

##    def getMARCValuebyRDF(self,marcField):
##        """
##  Extracts rule from the text of a bibframe.org/vocab/ rdf file
##  and applies the rule to the marc_record, and returns the 
##  value. This should be developed further as grammer of
##  RDF bfabstract:marcField becomes known.
##
##  :param marcField: etree marcField element
##  """
##        output = None
##  rule_txt = marcField.text
##  if marc_fld_re.search(rule_txt):
##            output = []
##            rules = marc_fld_re.findall(rule_txt)
##            for rule in rules:
##                marc_field,indicators,subfields = rule[0],rule[1],rule[2]
                
            
            
        

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

    def __init__(self, **kwargs):
        super(MARC21Ingester,self).__init__(**kwargs)
        self.entity_info = {}
        self.record = kwargs.get('marc_record',None)

    def __extract__(self,**kwargs):
        """
        Helper function takes a tag and list of rules and returns 
        either a set or a string of values 

        :kwarg tags: A list of MARC21 tags
        :kwarg indict1: A rule for indicator 1
        :kwarg indict2: A rule for indicator 2
        :kwarg subfields: A list of subfields
        """
        output = []
        tags = kwargs.get('tags',None)
        if tags is None:
            raise MARC21IngesterException("__extract__ helper function requires at least one MARC21 field tag")
        indicator1_rule = kwargs.get('indict1',None)
        indicator2_rule = kwargs.get('indict2',None)
        subfields = kwargs.get('subfields',None)
        fields = self.record.get_fields(tags)
        for field in fields:
            if indicator1_rule is not None:
                if not eval(indicator1_rule,field.indicator1):
                   continue
            if indicator2_rule is not None:
                if not eval(indicator2_rule,field.indicator2):
                    continue 
            for subfield in field.get_subfields(subfields):
                output.append(subfield)
        if len(output) == 1:
            return output[0]
        elif len(output) > 1:
            return set(output)


class MARC21toFacets(MARC21Ingester):
    """
     MARC21toFacets creates a MARCR annotations to be associated with
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
        facet_key = "bibframe:Annotation:Facet:Access:{0}".format(access)
        self.annotation_ds.sadd(facet_key, instance.redis_key)
        self.instance_ds.sadd("{0}:hasAnnotation".format(instance.redis_key),
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
        facet_key = "bibframe:Annotation:Facet:Format:{0}".format(
            getattr(instance,'rda:carrierTypeManifestation'))
        self.annotation_ds.sadd(facet_key, instance.redis_key)
        self.annotation_ds.zadd('bibframe:Annotation:Facet:Formats',
            float(self.annotation_ds.scard(facet_key)),
            facet_key)
        instance_annotation_key = "{0}:hasAnnotation".format(instance.redis_key)
        self.instance_ds.sadd("{0}:hasAnnotation".format(
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
            facet_key = "bibframe:Annotation:Facet:LOCFirstLetter:{0}".format(
                lc_facet)
            self.annotation_ds.sadd(facet_key, creative_work.redis_key)
            self.creative_work_ds.sadd("{0}:hasAnnotation".format(
                creative_work.redis_key),
                facet_key)
            self.annotation_ds.hset(
                "bibframe:Annotation:Facet:LOCFirstLetters",
                lc_facet,
                row)
            self.annotation_ds.zadd(
                "bibframe:Annotation:Facet:LOCFirstLetters:sort",
                float(self.annotation_ds.scard(facet_key)),
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

        locations = marc21_facets.get_location(record)
        if len(locations) > 0:
            for location in locations:
                redis_key = "bibframe:Annotation:Facet:Location:{0}".format(
                    location[0])
                self.annotation_ds.sadd(redis_key, instance.redis_key)
                if not self.annotation_ds.hexists(
                    "bibframe:Annotation:Facet:Locations",
                    location[0]):
                    self.annotation_ds.hset(
                        "bibframe:Annotation:Facet:Locations",
                        location[0],
                        location[1])
                self.annotation_ds.zadd(
                    "bibframe:Annotation:Facet:Locations:sort",
                    float(self.annotation_ds.scard(redis_key)),
                    redis_key)
                self.instance_ds.sadd("{0}:hasAnnotation".format(instance.redis_key),
                                      redis_key)

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
        self.instance = Instance(primary_redis=self.instance_ds)
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
                    self.instance_ds.sadd('identifiers:{0}:invalid'.format(source_code),
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
            if a_subfield is not None:
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
                                self.entity_info[name].append(subfield)
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
                self.instance_ds.sadd('identifiers:CODEN:invalid',subfield)
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
                    self.instance_ds.sadd('identifiers:ean:invalid',z_subfield)
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
        isbn_field = self.record['020']
        isbn_values = []
        if isbn_field is not None:
            for subfield in isbn_field.get_subfields('a', 'z'):
                isbn_values.append(''.join(subfield))
            self.entity_info['rda:identifierForTheManifestation:isbn'] = \
            set(isbn_values)

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
                self.instance_ds.sadd("identifiers:issn:invalid",subfield)
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
        Extract's LCCN call-number from MARC21 record and
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
                self.instance_ds.sadd('identifiers:lccn:invalid',subfield_z)


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
                self.instance_ds.sadd("identifiers:legal-deposit:invalid",subfield)
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
                self.instance_ds.sadd('identifiers:nban:invalid',subfield)
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
                self.instance_ds.sadd("identifers:nbn:invalid",subfield)
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
                self.instance_ds.sadd("identifiers:report-number:invalid",
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
                self.instance_ds.sadd("identifiers:strn:invalid",subfield)
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
                self.instance_ds.sadd("identifiers:system-number:invalid",subfield)
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
        

class MARC21toBIBFRAME(Ingester):
    """
    MARC21toBIBFRAME takes a MARC21 record and ingests into BIBFRAME Redis
    datastore
    """

    def __init__(self, marc_record, **kwargs):
        super(MARC21toBIBFRAME, self).__init__(**kwargs)
        self.record = marc_record

    def ingest(self):
        self.marc2creative_work = MARC21toCreativeWork(
            annotation_ds=self.annotation_ds,
            authority_ds=self.authority_ds,
            instance_ds=self.instance_ds,
            marc_record=self.record,
            creative_work_ds=self.creative_work_ds)
        self.marc2creative_work.ingest()
        self.marc2instance = MARC21toInstance(
            annotation_ds=self.annotation_ds,
            authority_ds=self.authority_ds,
            instance_ds=self.instance_ds,
            marc_record=self.record,
            creative_work_ds=self.creative_work_ds)
        self.marc2instance.ingest()
        self.marc2instance.instance.instanceOf = self.marc2creative_work.creative_work.redis_key
        self.marc2instance.instance.save()
        self.creative_work_ds.sadd("{0}:bibframe:Instances".format(self.marc2creative_work.creative_work.redis_key),
                                   self.marc2instance.instance.redis_key)
        self.marc2library_holdings = MARC21toLibraryHolding(annotation_ds=self.annotation_ds,
                                                            authority_ds=self.authority_ds,
                                                            creative_work_ds=self.creative_work_ds,
                                                            instance_ds=self.instance_ds,
                                                            marc_record=self.record,
                                                            instance=self.marc2instance.instance)
        self.marc2library_holdings.ingest()
        if self.instance_ds.hexists(self.marc2instance.instance.redis_key,
                                    'hasAnnotation'):
            annotation = self.marc2instance.instance.hasAnnotation
            self.instance_ds.hdel(self.marc2instance.instance.redis_key,
                                  'hasAnnotation')
            self.instance_ds.sadd("{0}:hasAnnotation".format(self.marc2instance.instance.redis_key),
                                  annotation)
        generate_call_number_app(self.marc2instance.instance, 
                                 self.instance_ds,
                                 self.annotation_ds)
        self.marc2facets = MARC21toFacets(annotation_ds=self.annotation_ds,
                                          authority_ds=self.authority_ds,
                                          creative_work_ds=self.creative_work_ds,
                                          instance_ds=self.instance_ds,
                                          marc_record=self.record,
                                          creative_work=self.marc2creative_work.creative_work,
                                          instance=self.marc2instance.instance)
        self.marc2facets.ingest()



class MARC21toLibraryHolding(MARC21Ingester):
    """
    MARC21toLibraryHolding ingests a MARC record into the BIBFRAME Redis datastore
    """

    def __init__(self,**kwargs):
        super(MARC21toLibraryHolding,self).__init__(**kwargs)
        self.holding = None
        self.instance = kwargs.get('instance',None)


    def add_holding(self):
        """
        Creates a Library Holdings based on values in the entity
        """
        self.holding = Holding(primary_redis=self.annotation_ds)
        for key,value in self.entity_info.iteritems():
            setattr(self.holding,key,value)
        if self.instance is not None:
            self.holding.annotates = self.instance.redis_key
            self.holding.save()
            self.instance_ds.sadd("{0}:hasAnnotation".format(self.instance.redis_key),
                                  self.holding.redis_key)
            
        else:
            self.holding.save()


    def ingest(self):
        """
        Ingests a MARC21 record and creates a Library Holding resource that 
        annotates a Creative Work or Instance.
        """
        self.extract_ddc()
        self.extract_govdoc()
        self.extract_lcc()
        self.extract_cc_local()
        self.extract_udc()
        self.add_holding()

    def __extract_callnumber__(self,tags):
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
                                                  '060',
                                                  '061',
                                                  '070',
                                                  '071'])
        if len(lcc_values) > 0:
            self.entity_info['callno-lcc'] = lcc_values

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
            if local_090 is not None and not self.entity_info.has_key('lcc'):
                self.entity_info['callno-local'] = local_090.value()


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
                        self.authority_ds.sadd("identifiers:{0}:invalid".format(feature)) 
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
		    self.entity_info['foaf:givenName'] = raw_names[0]
                elif self.field.indicator1 == '1':
                    self.entity_info['foaf:familyName'] = raw_names.pop(0)
                    # Assigns the next raw_name to givenName 
                    for raw_name in raw_names:
                        tokens = raw_name.split(' ')
                        if len(tokens[0]) > 0:
                            if [".",",","/"].count(tokens[0][-1]) > 0:
                                tokens[0] = tokens[0][:-1]
                            self.entity_info['foaf:givenName'] = tokens[0]
            for title in self.field.get_subfields('b'):
                 if self.entity_info.has_key('foaf:title'):
                     if type(self.entity_info['foaf:title']) == list:
                         self.entity_info['foaf:title'].append(title)
                     else:
                         self.entity_info['foaf:title'] = list(self.entity_info['foaf:title'])
                 else:
                     self.entity_info['foaf:title'] = title

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
        if ['100','700','800'].count(self.field.tag)> -1:
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
                                        self.authority_ds)
        if type(result) == list:
            self.people = result
        else:
            self.person = result
            self.people.append(self.person)


class MARC21toSubjects(MARC21Ingester):
    """
    MARC21toWork ingests a MARC21 record into the BIBFRAME Redis datastore
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
        redis_pipeline = self.authority_ds.pipeline()

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
            subject_key = 'bibframe:Authority:Subject:Genre:{0}'.format(
                ''.join(self.field.get_subfields('a')))
            self.authority_ds.sadd(subject_key,
                self.creative_work.redis_key)
            self.subjects.append(subject_key)

    def extract_geographic(self):
        """
        Extracts Geographic Subject from MARC21 651 field
        """
        if self.field.tag == '651':
            subject_key = 'bibframe:Authority:Subject:Geographic:{0}'.format(
                ''.join(self.field.get_subfields('a')))
            self.subjects.append(subject_key)
            self.add_subdivision(subject_key)

    def extract_topical(self):
        """
        Extracts Topical Subject from MARC21 650 field
        """
        if ['650'].count(self.field.tag) > -1:
            subject_key = 'bibframe:Authority:Subject:{0}'.format(
                ''.join(self.field.get_subfields('a')))
            self.subjects.append(subject_key)
            self.add_subdivision(subject_key)

    def ingest(self):
        self.extract_geographic()
        self.extract_genre()
        self.extract_topical()


class MARC21toCreativeWork(MARC21Ingester):
    """
    MARC21toWork ingests a MARC21 record into the BIBFRAME Redis datastore
    """

    def __init__(self,**kwargs):
        """
        Creates a MARC21toWork Ingester
        """
        super(MARC21toCreativeWork,self).__init__(**kwargs)
        self.creative_work = None

    def extract_classification(self):
        """
        Extracts classification from MARC
        """
        class_vals = []
        fields = self.record.get_fields('084','086')
        for field in fields:
            if field.tag == '084':
                class_vals.append(field.value())
            if field.tag == '086':
                class_vals.append(field['a'])
        if len(class_vals) > 1:
            self.entity_info['classification'] = set(class_vals)
        elif len(class_vals) == 1:
            self.entity_info['classification'] = class_vals[0]

    def extract_class_ddc(self):
        """
        Extracts Dewey Decimal Classification from MARC record
        """
        ddc_vals = []
        fields = self.record.get_fields('082','083')
        for field in fields:
            if field.tag == '083':
                ddc_vals.append('-'.join(field.get_subfields('a','c')))
            if field.tag == '082':
                ddc_vals.append(''.join(field.get_subfields('a')))
        if len(ddc_vals) > 0:
            self.entity_info['class-ddc'] = set(ddc_vals)

    def extract_class_lcc(self):
        """
        Extracts Library of Congress Classification from MARC record
        """
        lcc_vals = []
        fields = self.record.get_fields('050','051','055','060','061','070','071')
        for field in fields:
            if field['a'] is not None:
                lcc_vals.append(field['a'])
        if len(lcc_vals) > 0:
            self.entity_info['class-lcc'] = set(lcc_vals)

    def extract_class_udc(self):
        """
        Extracts Universal Decimal Classification Number
        """
        udc_values = []
        fields = self.record.get_fields('080')
        for field in fields:
            udc_values.append(field.value())
        if len(udc_values) > 0:
            self.entity_info['class-udc'] = set(udc_values)

    def extract_contentCoverage(self):
        """
        Extracts Nature of Content
        """
        coverages = []
        fields = self.record.get_fields('518','513','522')
        for field in fields:
            if field.tag == '518':
                if field['a'] is not None:
                    coverages.append(field['a'])
            if field.tag == '513':
                if field['b'] is not None:
                    coverages.append(field['b'])
            if field.tag == '522':
                if field['a'] is not None:
                    coverages.append(field['a'])
        if len(fields) > 0:
            self.entity_info['contentCoverage'] = set(fields)



    def extract_contentNature(self):
        """
        Extracts Nature of Content
        """
        content_natures = []
        fields = self.record.get_fields('245','513','008','336')
        for field in fields:
            if field.tag == '245':
                if field['k'] is not None:
                    content_natures.append(field['k'])
            if field.tag == '513':
                if field['a'] is not None:
                    content_natures.append(field['a'])
            if field.tag == '008':
                pass #! TODO need a look-up on 008 BK and CR
            if field.tag == '336':
                if field['a'] is not None:
                    content_natures.append("{0}(term)".format(field['a']))
                if field['b'] is not None:
                    content_natures.append("{0}(code)".format(field['b']))
        if len(content_natures) > 0:
            self.entity_info['contentNature'] = set(content_natures)
                                            
            

        
    def extract_creditNotes(self):
        """
        Extracts creditNotes from MARC
        """
        credit_notes = []
        fields = self.record.get_fields('508')
        for field in fields:
            credit_notes.append("Credits: {0}".format(field['a']))
        if len(credit_notes) > 0:
            self.entity_info['creditNote'] = set(credit_notes)

    def extract_creators(self):
        """
        Extracts and associates bibframe:Authority:Person entities creators
        work.
        """
        people_keys = []
        for field in self.record.get_fields('100','700','800'):
            if field is not None:
                people_ingester = MARC21toPerson(redis=self.authority_ds,
                                                 authority_ds=self.authority_ds,
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

    def __extract_other_std_id__(self,
                                 tag,
                                 source_code):
        """
        Helper function for isan, istc and other standard fields 

        :param tag: Required MARC field number
        :param indicator1: Value of indicator, defaults to 7
        """
        output = []
        fields = self.record.get_fields(tag)
        for field in fields:    
            if field.indicator1 == '7':
                extracted_code = field['2']
                if extracted_code == source_code:
                    for subfield in field.get_subfields('a','z'):
                        output.append(subfield)
        return output
                                      
    def extract_intendedAudience(self):
        """
        Extracts intendedAudience
        """
        audiences = []
        fields = self.record.get_fields('008','521')
        for field in fields:
            if field.tag == '008':
                pass #! TODO extract type and do look up for value
            if field.tag == '521':
                subfield_a_lst = field.get_subfields('a')
                for subfield in subfield_a_lst:
                    if field.indicator1 == '0':
                        audiences.append("Reading grade level {0}".format(subfield))
                    elif field.indicator1 == '1':
                        audiences.append("Interest age level {0}".format(subfield))
                    elif field.indicator1 == '2':
                        audiences.append("Interest grade level {0}".format(subfield))
                    elif field.indicator1 == '3':
                        audiences.append("Special audiences {0}".format(subfield))
                    elif field.indicator1 == '4':
                        audiences.append("Motivation/interest level {0}".format(subfield))
        if len(audiences) > 0:
            self.entity_info['intendedAudience'] = set(audiences)
                    
                

    def extract_isan(self):
        """
        Extracts International Standard Audiovisual Number (isan)
        """
        isan_vals = self.__extract_other_std_id__('024','isan')
        if len(isan_vals) > 1:
            self.entity_info["isan"] = set(isan_vals)
        elif len(isan_vals) == 1:
            self.entity_info["isan"] = isan_vals[0]
        

    def extract_istc(self):
        """
        Extracts International Standard Text code (istc)
        """
        isan_vals = self.__extract_other_std_id__('024','istc')
        if len(isan_vals) > 1:
            self.entity_info["istc"] = set(isan_vals)
        elif len(isan_vals) == 1:
            self.entity_info["istc"] = isan_vals[0]

    def extract_iswc(self):
        """
        Extracts International Standard Mustic Work Code (iswc)
        """
        isan_vals = self.__extract_other_std_id__('024','iswc')
        if len(isan_vals) > 1:
            self.entity_info["iswc"] = set(isan_vals)
        elif len(isan_vals) == 1:
            self.entity_info["iswc"] = isan_vals[0]
    
    def extract_issnl(self):
        """
        Extracts linking International Standard Serial Number
        """
        issnl_nums = []
        fields = self.record.get_fields('022')
        for field in fields:
            for subfield in field.get_subfields('1','m'):
                issnl_nums.append(subfield)
        if len(issnl_nums) > 0:
            self.entity_info["issn-l"] = set(issnl_nums)
                                           
    def extract_note(self):
        """
        Extracts the note for the work
        """
        notes = []
        fields = self.record.get_fields('500')
        for field in fields:
            subfield3 = field['3']
            if subfield3 is not None:
                notes.append("{0} {1}".format(subfield3,
                                              ''.join(field.get_subfields('a'))))
        if len(notes) > 0:
            self.entity_info["note"] = set(notes)
            
    def extract_performerNote(self):
        """
        Extracts performerNote
        """
        notes = []
        fields = self.record.get_fields('511')
        for field in fields:
            notes.append("Cast: {0}".format(''.join(field.get_subfields('a'))))
        if len(notes) > 0:
            self.entity_info["performerNote"] = set(notes)

    def extract_subjects(self):
        """
        Extracts amd associates bibframe:Authority:rda:Subjects entities
        with the creators work.
        """
        subject_keys = []


    def extract_title(self):
        """
        Extracts rda:titleProper from MARC21 record
        """
        slash_re = re.compile(r"/$")
        title_field = self.record['245']
        if title_field is not None:
            raw_title = ''.join(title_field.get_subfields('a'))
            if slash_re.search(raw_title):
                raw_title = slash_re.sub("",raw_title).strip()
            subfield_b = ' '.join(title_field.get_subfields('b'))
            if slash_re.search(subfield_b):
                subfield_b = slash_re.sub("",subfield_b).strip()
            raw_title += ' {0}'.format(subfield_b)
            if raw_title.startswith("..."):
                raw_title = raw_title.replace("...","")
            self.entity_info['title'] = {'rda:preferredTitleForTheWork':raw_title,
			'sort':raw_title.lower()}
            indicator_one = title_field.indicators[1]
            try:
                indicator_one = int(indicator_one)
            except ValueError:
                indicator_one = 0
            if int(indicator_one) > 0:
                self.entity_info['variantTitle'] = raw_title[indicator_one:]
                self.entity_info['title']['sort'] = self.entity_info['variantTitle']

              

    def get_or_add_work(self):
        """
        Method either returns a new Work or an existing work based
        on a similarity metric, basic similarity is 100% match
        (i.e. all fields must match or a new work is created)

        This method could use other Machine Learning techniques to improve
        the existing match with mutliple and complex rule sets. 
        """
        if self.entity_info.has_key('bibframe:Instances'):
            self.entity_info['bibframe:Instances'] = set(self.entity_info['bibframe:Instances'])
        # If the title matches an existing Work's title and the creative work's creators, 
        # assumes that the Creative Work is the same.
        if self.entity_info.has_key('title'):
            cw_title_keys = search_title(self.entity_info['title']['rda:preferredTitleForTheWork'],
                                         self.creative_work_ds)
            for creative_wrk_key in cw_title_keys:
                creator_keys = self.creative_work_ds.smembers(
                    "{0}:associatedAgent".format(creative_wrk_key))
                if self.entity_info.has_key('rda:isCreatedBy'):
                    existing_keys = creator_keys.intersection(self.entity_info['rda:isCreatedBy'])
                    if len(existing_keys) == 1:
                        self.creative_work = Work(primary_redis=self.creative_work_ds,
                                                  redis_key=creative_wrk_key)
            if not self.creative_work:
                self.creative_work = Work(primary_redis=self.creative_work_ds)
                for key, value in self.entity_info.iteritems():
                    setattr(self.creative_work,key,value)
                                    

            self.creative_work.save()
        else:
            # Work does not have a Title, this should be manditory but requires human
            # investigation.
            error_mrc_file = open(os.path.join(PROJECT_HOME,
                                               "bibframe",
                                               "errors",
                                               "missing-title-{0}.mrc".format(time.mktime(time.gmtime()))),
                                  "wb")
            error_writer = pymarc.MARCWriter(error_mrc_file)
            error_writer.write(self.record)
            error_mrc_file.close()



    def ingest(self):
        """
        Method ingests a MARC21 record into the BIBFRAME datastore

        :param record: MARC21 record
        """
        self.extract_classification()
        self.extract_class_ddc()
        self.extract_class_lcc()
        self.extract_class_udc()
        self.extract_contentCoverage()
        self.extract_contentNature()
        self.extract_creditNotes()
        self.extract_intendedAudience()
        self.extract_isan()
        self.extract_istc()
        self.extract_iswc()
        self.extract_issnl()
        self.extract_title()
        self.extract_creators()
        self.extract_note()
        self.extract_performerNote()
        self.get_or_add_work()
        # Adds work to creators
        if self.creative_work is not None:
            if self.creative_work.associatedAgent is not None:
                for creator_key in list(self.creative_work.associatedAgent):
                    creator_set_key = "{0}:rda:isCreatorPersonOf".format(creator_key)
                    self.authority_ds.sadd(creator_set_key,
                                           self.creative_work.redis_key)
            self.creative_work.save()
            generate_title_app(self.creative_work,self.creative_work_ds)
        super(MARC21toCreativeWork, self).ingest()





def ingest_marcfile(**kwargs):
    marc_filename = kwargs.get("marc_filename")
    annotation_ds = kwargs.get('annotation_redis')
    authority_ds = kwargs.get('authority_redis')
    creative_work_ds = kwargs.get("creative_work_redis")
    instance_ds =kwargs.get("instance_redis")
    if marc_filename is not None:
        marc_file = open(marc_filename,'rb')
        count = 0
        marc_reader = pymarc.MARCReader(marc_file,
                                        utf8_handling='ignore')
        start_time = datetime.datetime.now()
        sys.stderr.write("Starting at {0}\n".format(start_time.isoformat()))
        for record in marc_reader:
            ingester = MARC21toBIBFRAME(annotation_ds=annotation_ds,
                                        authority_ds=authority_ds,
                                        instance_ds=instance_ds,
                                        marc_record=record,
                                        creative_work_ds=creative_work_ds)
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
