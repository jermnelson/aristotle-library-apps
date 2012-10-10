"""
 :mod:`ingesters` Module ingests MARC21 and MODS records into a MARCR-Redis datastore
 controlled by the MARCR app.
"""
__author__ = "Jeremy Nelson"

import datetime,re,pymarc
from app_helpers import Annotation,CorporateBody,Person,Work,Instance
from call_number.redis_helpers import generate_call_number_app
from title_search.search_helpers import generate_title_app

import redis,datetime,pymarc
try:
    import aristotle.settings as settings
    WORK_REDIS = settings.WORK_REDIS
    INSTANCE_REDIS = settings.INSTANCE_REDIS
    AUTHORITY_REDIS = settings.AUTHORITY_REDIS
    ANNOTATION_REDIS = settings.ANNOTATION_REDIS
    OPERATIONAL_REDIS = settings.OPERATIONAL_REDIS
except ImportError, e:
    redis_host = '0.0.0.0'
    WORK_REDIS = redis.StrictRedis(port=6380)
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

        :keyword work_ds: Work Redis datastore, defaults to WORK_REDIS
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
        self.work_ds = kwargs.get('work_ds',WORK_REDIS)

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


class MARC21toInstance(MARC21Ingester):
    """
    MARC21toInstance ingests a MARC record into the MARCR Redis datastore
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
        Ingests a MARC21 record into a MARCR Instance Redis datastore
        """
        self.extract_ils_bibnumber()
        self.extract_lccn()
        self.extract_sudoc()
        self.extract_local()
        self.add_instance()
        generate_call_number_app(self.instance,self.instance_ds)

class MARC21toMARCR(Ingester):
    """
    MARC21toMARCR takes a MARC21 record and ingests into MARCR Redis
    datastore
    """

    def __init__(self,marc_record):
        super(MARC21toMARCR,self).__init__(**kwargs)
        self.record = marc_record

    def ingest(self):
        marc2work = MARC21toWork(annotation_ds=self.annotation_ds,
                                 authority_ds=self.authority_ds,
                                 instance_ds=self.instance_ds,
                                 marc_record=self.record,
                                 work_ds=self.work_ds)
        marc2work.ingest()
        marc2instance = MARC21toInstance(annotation_ds=self.annotation_ds,
                                         authority_ds=self.authority_ds,
                                         instance_ds=self.instance_ds,
                                         marc_record=self.record,
                                         work_ds=self.work_ds)
        marc2instance.ingest()
        if marc2work.work.attributes.has_key('marcr:Instances'):
            marc2work.work.attributes['marcr:Instances'].append(marc2instance.instance.redis_key)
        else:
            marc2work.work.attributes['marcr:Instances'] = [marc2instance.instance.redis_key]
            
        

    

class MARC21toPerson(MARC21Ingester):
    """
    MARC21toPerson ingests a MARC record into the MARCR Redis datastore
    """

    def __init__(self,**kwargs):
        self.person = None
        super(MARC21toPerson,self).__init__(**kwargs)

    def get_or_add_person(self):
        """
        Method either returns a new Person or an existing Person based
        on a similarity metric
        """
        pass

    def extractDates(self):
        """
        Extracts rda:dateOfBirth and rda:dateOfDeath from MARC21 record
        """
        date_range = re.compile(r"(\d+)-*(\d*)")
        for tag in ['100','700','800']:
            field = self.record[tag]
            if field is not None:
                if ['0','1'].count(field.indicators[0]) > -1:
                    raw_dates = ''.join(field.get_subfields('d'))
                    date_result = date_range.search(raw_dates)
                    if date_result is not None:
                        groups = date_result.groups()
                        if len(groups[0]) > 0:
                            self.entity_values['rda:dateOfBirth'] = groups[0]
                        if len(groups[1]) > 0:
                            self.entity_values['rda:dateOfDeath'] = groups[1]
                    else:
                        raise ValueError("Raw dates: {0} not matched".format(raw_dates))
        if self.record['542'] is not None:
            field542b = self.record['542'].get_subfields('b')
            if len(field542b) > 0:
                self.entity_values['rda:dateOfDeath'] = ''.join(field542b)
                

    def extract_preferredNameForThePerson(self):
        """
        Extracts RDA's preferredNameForThePerson from MARC21 record
        """
        preferred_name = []
        for tag in ['100','700','800']:
            field = self.record[tag]
            if field is not None:
                if ['0','1'].count(field.indicators[0]) > -1:
                    preferred_name.extend(field.get_subfields('a','b'))
        self.entity_values['rda:preferredNameForThePerson'] = ' '.join(preferred_name)
                        
                

    def ingest(self):
        self.extract_preferredNameForThePerson()
        self.extractDates()
        self.extractTitle()                              

class MARC21toWork(MARC21Ingester):
    """
    MARC21toWork ingests a MARC record into the MARCR Redis datastore
    """

    def __init__(self,**kwargs):
        """
        Creates a MARC21toWork Ingester
        """
        super(MARC21toWork,self).__init__(**kwargs)
        self.work = None

    def extract_people(self):
        """
        Extracts and associates marcr:Authority:Person entities with
        work.
        """
        pass

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
                subfield_b = slash_re.sub("",raw_title).strip()
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
        if self.entity_info.has_key('marcr:Instances'):
            self.entity_info['marcr:Instances'] = set(self.entity_info['marcr:Instances'])
        self.work = Work(redis=self.work_ds,
                         attributes=self.entity_info)            
        self.work.save()
    

    def ingest(self):
        """
        Method ingests a MARC21 record into the MARCR datastore

        :param record: MARC21 record
        """
        self.extract_title()
        self.get_or_add_work()
        generate_title_app(self.work,self.work_ds)
        super(MARC21toWork,self).ingest()

def ingest_marcfile(**kwargs):
    marc_filename = kwargs.get("marc_filename")
    annotation_ds = kwargs.get('annotation_redis')
    authority_ds = kwargs.get('authority_redis')
    work_ds = kwargs.get("work_redis")
    instance_ds =kwargs.get("instance_redis")
    if marc_filename is not None:
        count = 0
        marc_reader = pymarc.MARCReader(open(marc_filename),
                                        utf8_handling='ignore')
        for record in marc_reader:
            ingester = MARC21toMARCR(annotation_ds=annotation_ds,
                                     authority_ds=authority_ds,
                                     instance_ds=instance_ds,
                                     marc_record=record,
                                     work_ds=work_ds)
            ingester.ingest()
            if count%1000:
                sys.stderr.write(".")
            else:
                sys.stderr.write(str(count))
            count += 1
            
    
