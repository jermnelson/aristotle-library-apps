"""
 :mod:`ingesters` Module ingests MARC21 and MODS records into a MARCR-Redis datastore
 controlled by the MARCR app.
"""
__author__ = "Jeremy Nelson"

import datetime,re,pymarc,sys,logging
from bibframe_models import Annotation,CorporateBody,CreativeWork,Instance,Person
from call_number.redis_helpers import generate_call_number_app
from person_authority.redis_helpers import get_or_generate_person
from title_search.search_helpers import generate_title_app

import marc21_facets

import redis,datetime,pymarc
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

    def __init__(self,**kwargs):
        """
        Initializes Ingester

        :keyword creative_work_ds: Work Redis datastore, defaults to CREATIVE_WORK_REDIS
        :keyword instance_ds: Instance Redis datastore, defaults to
                              INSTANCE_REDIS
        :keyword authority_ds: Authority Redis datastore, default to
                               AUTHORITY_REDIS
        :keyword annotation_ds: Annotation Redis datastore, defaults to
                                ANNOTATION_REDIS
        """
        self.annotation_ds = kwargs.get('annotation_ds',ANNOTATION_REDIS)
        self.authority_ds = kwargs.get('authority_ds',AUTHORITY_REDIS)
        self.instance_ds = kwargs.get('instance_ds',INSTANCE_REDIS)
        self.creative_work_ds = kwargs.get('creative_work_ds',CREATIVE_WORK_REDIS)

    def ingest(self):
        pass
        
        
class MARC21Helpers(object):
    """
    MARC21 Helpers for MARC21 Ingester classes
    """

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
        
            
class MARC21Ingester(Ingester):

    def __init__(self,**kwargs):
        self.entity_info = {}
        self.record = kwargs.get('marc_record',None)
        super(MARC21Ingester,self).__init__(**kwargs)



class MARC21toFacets(MARC21Ingester):
    """
     MARC21toFacets creates a MARCR annotations to be associated with
     either a Work or Instance.
    """

    def __init__(self,**kwargs):
        self.facets = None
	self.creative_work = kwargs.get('creative_work')
	self.instance = kwargs.get('instance')
	super(MARC21toFacets,self).__init__(**kwargs)


    def add_access_facet(self,**kwargs):
        """
	Creates a bibframe:Annotation:Facet:Access based on 
	extracted info from the MARC21 Record

        :param instance: BIBFRAME Instance, defaults to self.instance
	:param record: MARC21 record, defaults to self.marc_record
	"""
	instance = kwargs.get("instance",self.instance)
	record = kwargs.get("record",self.record)
	access = marc21_facets.get_access(record)
	facet_key = "bibframe:Annotation:Facet:Access:{0}".format(access)
	self.annotation_ds.sadd(facet_key,instance.redis_key)
	self.instance_ds.sadd("{0}:Annotations:facets".format(instance.redis_key),
			      facet_key)


    def add_format_facet(self,**kwargs):
	"""
	Creates a bibframe:Annotation:Facet:Format based on the 
	rda:carrierTypeManifestation property of the marcr:Instance

        :param instance: BIBFRAME Instance, defaults to self.instance
	"""
	# Extract's the Format facet value from the Instance and
	# creates an Annotation key that the instance's redis key
	# is either added to an existing set or creates a new 
	# sorted set for the facet marcr:Annotation
	instance = kwargs.get("instance",self.instance)
	facet_key = "bibframe:Annotation:Facet:Format:{0}".format(instance.attributes['rda:carrierTypeManifestation'])
	self.annotation_ds.sadd(facet_key,instance.redis_key)
	self.instance_ds.sadd("{0}:Annotations:facets".format(instance.redis_key),facet_key)


    def add_lc_facet(self,**kwargs):
        """
	Adds bibframe:CreativeWork to the bibframe:Annotation:Facet:LOCLetter facet
	based on extracted info from the MARC21 Record

        :param creative_work: BIBFRAME CreativeWork, defaults to self.creative_work
	:param record: MARC21 record, defaults to self.marc_record
	"""
	creative_work = kwargs.get('creative_work',self.creative_work)
	record = kwargs.get('record',self.record)
	lc_facet,lc_facet_desc = marc21_facets.get_lcletter(record)
	for row in lc_facet_desc:
	    facet_key = "bibframe:Annotation:Facet:LOCFirstLetter:{0}".format(lc_facet)
	    self.annotation_ds.sadd(facet_key,creative_work.redis_key)
	    self.creative_work_ds.sadd("{0}:Annotations:facets".format(creative_work.redis_key),facet_key)
	    self.annotation_ds.hset("bibframe:Annotation:Facet:LOCFirstLetters",lc_facet,row)
    
    def add_locations_facet(self,**kwargs):
        """
	Method takes an instance and a MARC21 record, extracts all CC's
	location (holdings) codes from the MARC21 record and adds the instance key
	to all of the holdings facets.

	:param instance: BIBFRAME Instance, defaults to self.instance
	:param record: MARC21 record, defaults to self.marc_record
	"""
        instance = kwargs.get("instance",self.instance)
	record = kwargs.get("record",self.record)

	locations = marc21_facets.get_location(record)
	if len(locations) > 0:
	    for location in locations:
		redis_key = "bibframe:Annotation:Facet:Location:{0}".format(location[0])
		self.annotation_ds.sadd(redis_key,instance.redis_key)
		if not self.annotation_ds.hexists("bibframe:Annotation:Facet:Locations",location[0]):
		    self.annotation_ds.hset("bibframe:Annotation:Facet:Locations",
				            location[0],
					    location[1])
		self.instance_ds.sadd("{0}:Annotations:facets".format(instance.redis_key),
				      redis_key)

    def ingest(self,**kwargs):
	"""
	Method runs all of the Facet generation methods

	:param creative_work: BIBFRAME CreativeWork, defaults to self.creative_work
	:param instance: BIBFRAME Instance, default to self.instnace
	:param record: MARC21 record, defaults to self.marc_record
	"""
        creative_work = kwargs.get('creative_work',self.creative_work)
        instance = kwargs.get("instance",self.instance)
	record = kwargs.get('record',self.record)
        self.add_access_facet(instance=instance,
			      record=record)
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

    def __init__(self,**kwargs):
        self.instance = None
        super(MARC21toInstance,self).__init__(**kwargs)
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
	self.entity_info['rda:carrierTypeManifestation'] = marc21_facets.get_format(self.record)
                                 

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
            for subfield in isbn_field.get_subfields('a','z'):
                isbn_values.append(''.join(subfield))
            self.entity_info['rda:identifierForTheManifestation:isbn'] = set(isbn_values)

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
            self.entity_info['rda:identifierForTheManifestation:issn'] = set(issn_values)            
            
    def extract_lccn(self):
        """
        Extract's LCCN call-number from MARC21 record and
        saves as a rda:identifierForTheManifestation
        """
        lccn_field = self.record['050']
        if lccn_field is not None:
            self.entity_info['rda:identifierForTheManifestation']['lccn'] = lccn_field.value()
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
        self.extract_local()
        self.add_instance()
        generate_call_number_app(self.instance,self.instance_ds)

class MARC21toBIBFRAME(Ingester):
    """
    MARC21toBIBFRAME takes a MARC21 record and ingests into BIBFRAME Redis
    datastore
    """

    def __init__(self,marc_record,**kwargs):
        super(MARC21toBIBFRAME,self).__init__(**kwargs)
        self.record = marc_record

    def ingest(self):
        self.marc2creative_work = MARC21toCreativeWork(annotation_ds=self.annotation_ds,
                                                       authority_ds=self.authority_ds,
                                                       instance_ds=self.instance_ds,
                                                       marc_record=self.record,
                                                       creative_work_ds=self.creative_work_ds)
        self.marc2creative_work.ingest()
        self.marc2instance = MARC21toInstance(annotation_ds=self.annotation_ds,
                                              authority_ds=self.authority_ds,
                                              instance_ds=self.instance_ds,
                                              marc_record=self.record,
                                              creative_work_ds=self.creative_work_ds)
        self.marc2instance.ingest()
        self.marc2instance.instance.attributes["bibframe:CreativeWork"] = self.marc2creative_work.creative_work.redis_key
        self.marc2instance.instance.save()
        if self.marc2creative_work.creative_work.attributes.has_key('bibframe:Instances'):
            self.marc2creative_work.creative_work.attributes['bibframe:Instances'].append(self.marc2instance.instance.redis_key)
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

    def __init__(self,**kwargs):
        super(MARC21toPerson,self).__init__(**kwargs)
        self.person = None
        self.people = []
        self.field = kwargs.get("field",None)

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
            self.entity_info['rda:preferredNameForThePerson'] = ' '.join(preferred_name)
                        
                

    def ingest(self):
        self.extract_preferredNameForThePerson()
        self.extractDates()
        #print("In ingest after extracting info {0}".format(self.entity_info))
        result = get_or_generate_person(self.entity_info,
                                        self.authority_ds)
        #print("Redis key is {0}".format(self.people))
        if type(result) == list:
            self.people = result
        else:
            self.person = result
            self.people.append(self.person)

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

    def extract_creators(self):
        """
        Extracts and associates marcr:Authority:Person entities creators
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
            self.entity_info['rda:Title'] = {'rda:preferredTitleForTheWork':raw_title}
            indicator_one = title_field.indicators[1]
            try:
                indicator_one = int(indicator_one)
            except ValueError:
                indicator_one = 0
            if int(indicator_one) > 0:
                self.entity_info['rda:Title']['rda:variantTitleForTheWork:sort'] = raw_title[indicator_one:]

    def get_or_add_work(self):
        """
        Method either returns a new Work or an existing work based
        on a similarity metric, basic similarity is 100% match
        (i.e. all fields must match or a new work is created)
        """
        if self.entity_info.has_key('bibframe:Instances'):
            self.entity_info['bibframe:Instances'] = set(self.entity_info['bibframe:Instances'])
        self.creative_work = CreativeWork(redis=self.creative_work_ds,
                                          attributes=self.entity_info)            
        self.creative_work.save()
    

    def ingest(self):
        """
        Method ingests a MARC21 record into the BIBFRAME datastore

        :param record: MARC21 record
        """
        self.extract_title()
        self.extract_creators()
        self.get_or_add_work()
        # Adds work to creators
        if self.creative_work.attributes.has_key('rda:creator'):
            for creator_key in self.creative_work.attributes['rda:creator']:
                creator_set_key = "{0}:rda:isCreatorPersonOf".format(creator_key)
                self.authority_ds.sadd(creator_set_key,
                                       self.creative_work.redis_key)                
        self.creative_work.save()
        generate_title_app(self.creative_work,self.creative_work_ds)
        super(MARC21toCreativeWork,self).ingest()

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
        print("Starting at {0}".format(start_time.isoformat()))
        for record in marc_reader:
            ingester = MARC21toBIBFRAME(annotation_ds=annotation_ds,
                                        authority_ds=authority_ds,
                                        instance_ds=instance_ds,
                                        marc_record=record,
                                        creative_work_ds=creative_work_ds)
            ingester.ingest()
            if count%1000:
##                print(count)
                sys.stderr.write(".")
            else:
                sys.stderr.write(str(count))
                
            count += 1
        end_time = datetime.datetime.now()
        print("Finished at {0}".format(end_time.isoformat()))
        print("Total time elapsed is {0} seconds".format((end_time-start_time).seconds))
        
        return count
            
    
