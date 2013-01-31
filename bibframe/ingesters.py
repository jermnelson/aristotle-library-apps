"""
 :mod:`ingesters` Module ingests MARC21 and MODS records into a MARCR-Redis datastore
 controlled by the MARCR app.
"""
__author__ = "Jeremy Nelson"

import datetime, re, pymarc, os, sys,logging, redis, time
from bibframe.models import Annotation, Organization, Work, Instance, Person
from call_number.redis_helpers import generate_call_number_app
from person_authority.redis_helpers import get_or_generate_person
from aristotle.settings import PROJECT_HOME
from title_search.redis_helpers import generate_title_app,search_title
import marc21_facets
from lxml import etree
from rdflib import RDF,RDFS,Namespace
import json

STD_SOURCE_CODES = json.load(open(os.path.join(PROJECT_HOME,
                                               'bibframe',
                                               'fixures',
                                               'standard-id-src-codes.json'),
                                  'rb'))

BF = Namespace('http://bibframe.org/model-abstract/')


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





class Ingester(object):
    """
    Base Ingester class for ingesting metadata and bibliographic
    records into the MARCR Redis datastore.
    """

    def __init__(self, **kwargs):
        """
        Initializes Ingester

        :keyword creative_work_ds: Work Redis datastore, defaults to
                                   CREATIVE_WORK_REDIS
        :keyword instance_ds: Instance Redis datastore, defaults to
                              INSTANCE_REDIS
        :keyword authority_ds: Authority Redis datastore, default to
                               AUTHORITY_REDIS
        :keyword annotation_ds: Annotation Redis datastore, defaults to
                                ANNOTATION_REDIS
        """
        self.annotation_ds = kwargs.get('annotation_ds',
                                        ANNOTATION_REDIS)
        self.authority_ds = kwargs.get('authority_ds',
                                       AUTHORITY_REDIS)
        self.instance_ds = kwargs.get('instance_ds',
                                      INSTANCE_REDIS)
        self.creative_work_ds = kwargs.get('creative_work_ds',
                                           CREATIVE_WORK_REDIS)

    def ingest(self):
        pass

#MARC_FLD_RE = re.compile(r"(\d+)([-|w+])([-|w+])/(\w+)")
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



class MARC21Ingester(Ingester):

    def __init__(self, **kwargs):
        self.entity_info = {}
        self.record = kwargs.get('marc_record',None)
        super(MARC21Ingester,self).__init__(**kwargs)


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
        self.instance_ds.sadd("{0}:Annotations:facets".format(
            instance.redis_key),
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
            instance.attributes['rda:carrierTypeManifestation'])
        self.annotation_ds.sadd(facet_key, instance.redis_key)
        self.annotation_ds.zadd('bibframe:Annotation:Facet:Formats',
            float(self.annotation_ds.scard(facet_key)),
            facet_key)
        self.instance_ds.sadd("{0}:Annotations:facets".format(
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
            self.creative_work_ds.sadd("{0}:Annotations:facets".format(
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
                self.instance_ds.sadd("{0}:Annotations:facets".format(
                    instance.redis_key),
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
        self.instance = Instance(redis=self.instance_ds,
                                 attributes=self.entity_info)
        self.instance.save()

    def extract_carrier_type(self):
        """
        Extract's the RDA carrier type from a MARC21 record and
        saves result as an Instance's rda:carrierTypeManifestation,

        NOTE: method currently using CC's MARC21 mapping, needs to
        normalized to the controlled vocabulary of rda:carrierType
        """
        self.entity_info['rda:carrierTypeManifestation'] = \
        marc21_facets.get_format(self.record)


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
        issn_field = self.record['022']
        issn_values = []
        if issn_field is not None:
            for subfield in issn_field.get_subfields('a',
                                                     'y',
                                                     'z'):
                issn_values.append(''.join(subfield))
            self.entity_info['rda:identifierForTheManifestation:issn'] = \
            set(issn_values)

    def extract_lccn(self):
        """
        Extract's LCCN call-number from MARC21 record and
        saves as a rda:identifierForTheManifestation
        """
        lccn_field = self.record['050']
        if lccn_field is not None:
            self.entity_info['rda:identifierForTheManifestation']['lccn'] = \
            lccn_field.value()
        else:
            # Adds 090 value to lccn following CC standard practice
            local_090 = self.record['090']
            if local_090 is not None:
                self.entity_info['rda:identifierForTheManifestation']['lccn'] = local_090.value()

    def extract_local(self):
        """
        Extracts local call number MARC21 record and
        saves as a rda:identifierForTheManifestation
        """
        local_099 = self.record['099']
        if local_099 is not None:
            self.entity_info['rda:identifierForTheManifestation']['local'] = local_099.value()
        else:
            local_090 = self.record['090']
            if local_090 is not None and not self.entity_info['rda:identifierForTheManifestation'].has_key('lccn'):
                self.entity_info['rda:identifierForTheManifestation']['local'] = local_090.value()

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


    def extract_sudoc(self):
        """
        Extracts sudoc call-number from MARC record and
        saves as a rda:identifierForTheManifestation
        """
        sudoc_field = self.record['086']
        if sudoc_field is not None:
            self.entity_info['rda:identifierForTheManifestation']['sudoc'] = sudoc_field.value()

    def ingest(self):
        """
        Ingests a MARC21 record into a BIBFRAME Instance Redis datastore
        """
        self.extract_carrier_type()
        self.extract_ils_bibnumber()
        self.extract_isbn()
        self.extract_issn()
        self.extract_lccn()
        self.extract_sudoc()
        self.extract_date_of_publication()
        self.extract_local()
        self.add_instance()
        generate_call_number_app(self.instance, self.instance_ds)


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
        self.marc2instance.instance.attributes["bibframe:CreativeWork"] = \
        self.marc2creative_work.creative_work.redis_key
        self.marc2instance.instance.save()
        if self.marc2creative_work.creative_work.attributes.has_key('bibframe:Instances'):
            self.marc2creative_work.creative_work.attributes['bibframe:Instances'].add(self.marc2instance.instance.redis_key)
        else:
            self.marc2creative_work.creative_work.attributes['bibframe:Instances'] = [self.marc2instance.instance.redis_key,]
        self.marc2creative_work.creative_work.save()
        self.marc2facets = MARC21toFacets(annotation_ds=self.annotation_ds,
                              authority_ds=self.authority_ds,
                      creative_work_ds=self.creative_work_ds,
                      instance_ds=self.instance_ds,
                      marc_record=self.record,
                      creative_work=self.marc2creative_work.creative_work,
                      instance=self.marc2instance.instance)
        self.marc2facets.ingest()




class MARC21toPerson(MARC21Ingester):
    """
    MARC21toPerson ingests a MARC record into the BIBFRAME Redis datastore
    """

    def __init__(self, **kwargs):
        super(MARC21toPerson, self).__init__(**kwargs)
        self.person = None
        self.people = []
        self.field = kwargs.get("field", None)

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



    def ingest(self):
        self.extract_preferredNameForThePerson()
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
        for tag in ['100','700','800']:
            field = self.record[tag]
            if field is not None:
                people_ingester = MARC21toPerson(redis=self.authority_ds,
                                                 authority_ds=self.authority_ds,
                                                 field=field)
                people_ingester.ingest()
                for person in people_ingester.people:
                    people_keys.append(person.redis_key)
        if len(people_keys) > 0:
            self.entity_info['rda:creator'] = set(people_keys)

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
            self.entity_info['rda:Title'] = {'rda:preferredTitleForTheWork':raw_title,
                                             'sort':raw_title.lower()}
            indicator_one = title_field.indicators[1]
            try:
                indicator_one = int(indicator_one)
            except ValueError:
                indicator_one = 0
            if int(indicator_one) > 0:
                self.entity_info['rda:Title']['rda:variantTitleForTheWork'] = raw_title[indicator_one:]
                self.entity_info['rda:Title']['sort'] = self.entity_info['rda:Title']['rda:variantTitleForTheWork'].lower()

              

    def get_or_add_work(self):
        """
        Method either returns a new Work or an existing work based
        on a similarity metric, basic similarity is 100% match
        (i.e. all fields must match or a new work is created)
        """
        if self.entity_info.has_key('bibframe:Instances'):
            self.entity_info['bibframe:Instances'] = set(self.entity_info['bibframe:Instances'])
        # If the title matches an existing Work's title and the creative work's creators, 
        # assumes that the Creative Work is the same.
    if self.entity_info.has_key('rda:Title'):
            cw_title_keys = search_title(self.entity_info['rda:Title']['rda:preferredTitleForTheWork'],
                                         self.creative_work_ds)
            for creative_wrk_key in cw_title_keys:
                creator_keys = self.creative_work_ds.smembers("{0}:rda:creator".format(creative_wrk_key))
            if self.entity_info.has_key('rda:creator'):
                    existing_keys = creator_keys.intersection(self.entity_info['rda:creator'])
                    if len(existing_keys) == 1:
                        self.creative_work = Work(primary_redis=self.creative_work_ds,
                                                  redis_key=creative_wrk_key)
            if not self.creative_work:
                self.creative_work = Work(primary_redis=self.creative_work_ds,
                                          attributes=self.entity_info)

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
        self.extract_title()
        self.extract_creators()
        self.get_or_add_work()
        # Adds work to creators
        if self.creative_work is not None:
            if self.creative_work.attributes.has_key('rda:creator'):
                for creator_key in self.creative_work.attributes['rda:creator']:
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
