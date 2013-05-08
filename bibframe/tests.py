"""
 :mod:`tests` - Unit tests for the Bibliographic Framework App
"""
__author__ = "Jeremy Nelson"
import pymarc
import os
import redis
from django.test import TestCase
from bibframe.models import *
from bibframe.ingesters.MARC21 import *
from ingesters.MARC21 import MARC21toInstance,MARC21toBIBFRAME,MARC21toPerson,MARC21toCreativeWork
from ingesters.MARC21 import MARC21toFacets,MARC21toLibraryHolding,MARC21toSubjects
from aristotle.settings import PROJECT_HOME

try:
    from aristotle.settings import TEST_REDIS
except ImportError, e:
    TEST_REDIS = redis.StrictRedis(host="192.168.64.143",
                                   port=6385)

test_redis = TEST_REDIS

class ProcessKeyTest(TestCase):

    def setUp(self):
	self.timestamp = datetime.datetime.utcnow().isoformat()
        test_redis.hset('bf:CreativeWork:1',
			'created_on',
			self.timestamp)


    def test_process_key(self):
	self.assertEquals(process_key('bf:CreativeWork:1', test_redis)['created_on'],
			              self.timestamp)

	
    def test_process_key_exception(self):
        self.assertRaises(,
                          process_key,
                          'bf:CreativeWork:2', 
                          test_redis)

    def tearDown(self):
        test_redis.flushdb()


class SaveKeysTest(TestCase):

    def setUp(self):
        save_keys('test:entity:1','option',1,test_redis)
        save_keys('test:entity:1','option2',set([2,]),test_redis)
        save_keys('test:entity:1','option3',set([3,4]),test_redis)


    def test_save_keys_string(self):
        self.assertEquals(test_redis.hget('test:entity:1','option'),
                          '1')

    def test_save_keys_set(self):
        self.assertEquals(test_redis.hget('test:entity:1','option2'),
                          '2')
        self.assertEquals(test_redis.smembers('test:entity:1:option3'),
                          set(['3','4']))
    

    def tearDown(self):
        test_redis.flushdb()

class RedisBibframeInterfaceTest(TestCase):

    def setUp(self):
        self.minimal_instance = RedisBibframeInterface()

    def test_init(self):
        self.assert_(not self.minimal_instance.primary_redis)
	self.assert_(not self.minimal_instance.redis_key)

    def test_save_execeptions(self):
	self.assertRaises(ValueError,self.minimal_instance.save)

    def tearDown(self):
        test_redis.flushdb()

class ResourceTest(TestCase):

    def setUp(self):
        self.resource = Resource(primary_redis=test_redis)

    def test_init(self):
        self.assert_(self.resource.primary_redis is not None)

    def tearDown(self):
        test_redis.flushdb()
        

class AuthorityTest(TestCase):

    def setUp(self):
        self.new_base_authority = Authority(primary_redis=test_redis)
	self.created_on = datetime.datetime.utcnow().isoformat()
	test_redis.hset('bibframe:Authority:1','created_on',self.created_on)
        self.base_authority = Authority(primary_redis=test_redis,
                                        redis_key="bibframe:Authority:1",
                                        hasAnnotation=set('bibframe:Annotation:1'))
	self.base_authority.save()

    def test_init(self):
	self.assert_(self.new_base_authority.primary_redis is not None)
	self.assert_(test_redis.exists(self.base_authority.redis_key))
        self.assertEquals(self.base_authority.redis_key,
                          "bibframe:Authority:1")

    def test_hasAnnotation(self):
        self.assertEquals(self.base_authority.hasAnnotation,
                          set('bibframe:Annotation:1'))
	self.assertEquals(test_redis.smembers('bibframe:Authority:1:hasAnnotation'),
			  set('bibframe:Annotation:1'))

    def tearDown(self):
        test_redis.flushdb()

class PersonAuthorityTest(TestCase):

    def setUp(self):
        self.person = Person(primary_redis=test_redis,
                             identifier={'loc':'http://id.loc.gov/authorities/names/n86001949'},
                             label="David Foster Wallace",
                             hasAnnotation=set('bibframe:Annotation:1'),
                             isni='0000 0001 1768 6131')
        setattr(self.person,'rda:dateOfBirth','1962-04-21')
        setattr(self.person,'rda:dateOfDeath','2008-09-12')
        setattr(self.person,'rda:gender','male')
        setattr(self.person,'foaf:familyName','Wallace')
        setattr(self.person,'foaf:givenName','David')
        setattr(self.person,'rda:preferredNameForThePerson','Wallace, David Foster')
        self.person.save()

    def test_dateOfBirth(self):
        self.assertEquals(getattr(self.person,'rda:dateOfBirth'),
                          test_redis.hget(self.person.redis_key,
                                          'rda:dateOfBirth'))

    def test_dateOfDeath(self):
        self.assertEquals(getattr(self.person,'rda:dateOfDeath'),
                          test_redis.hget(self.person.redis_key,
                                          'rda:dateOfDeath'))
    def test_hasAnnotation(self):
        self.assertEquals(self.person.hasAnnotation,
                          set('bibframe:Annotation:1'))

    def test_init(self):
        self.assert_(self.person.primary_redis is not None)

    def test_isni(self):
        self.assertEquals(self.person.isni,
                          '0000 0001 1768 6131')

    def test_foaf(self):
        self.assertEquals(getattr(self.person,'foaf:givenName'),
                          'David')
        self.assertEquals(getattr(self.person,'foaf:givenName'),
                          test_redis.hget(self.person.redis_key,
                                          'foaf:givenName'))
        self.assertEquals(getattr(self.person,'foaf:familyName'),
                          'Wallace')
        self.assertEquals(getattr(self.person,'foaf:familyName'),
                          test_redis.hget(self.person.redis_key,
                                          'foaf:familyName'))
      

    def test_gender(self):
        self.assertEquals(getattr(self.person,'rda:gender'),
                          test_redis.hget(self.person.redis_key,
                                          'rda:gender'))

    def test_label(self):
        self.assertEquals(self.person.label,
                          "David Foster Wallace")

    def test_loc_id(self):
        self.assertEquals(self.person.identifier.get('loc'),
                          test_redis.hget("{0}:{1}".format(self.person.redis_key,
                                                           'identifier'),
                                          'loc'))

    def test_name(self):
        self.assertEquals(getattr(self.person,'rda:preferredNameForThePerson'),
                          test_redis.hget(self.person.redis_key,
                                          'rda:preferredNameForThePerson'))

    def test_save(self):
        self.assertEquals(self.person.redis_key,
                          "bibframe:Person:1")

    def tearDown(self):
        test_redis.flushdb()


##class MARC21toFacetsTest(TestCase):
##
##    def setUp(self):
##	self.marc_record = pymarc.Record()
##	self.marc_record.add_field(pymarc.Field(tag='994',
##	                           indicators=['0','0'],
##				   subfields=['a','ewwwn']))
##	self.marc_record.add_field(pymarc.Field(tag='994',
##	                           indicators=['0','0'],
##				   subfields=['a','tarfc']))
##	self.marc_record.add_field(pymarc.Field(tag='994',
##	                           indicators=['0','0'],
##				   subfields=['a','tgr']))
##
##	self.facet_ingester = MARC21toFacets(annotation_ds=test_redis,
##			                     authority_ds=test_redis,
##					     instance_ds=test_redis,
##					     creative_work_ds=test_redis,
##					     marc_record=self.marc_record)
##
##    def test_access_facet(self):
##	instance = Instance(redis=test_redis)
##	instance.save()
##	self.facet_ingester.add_access_facet(instance=instance,
##			                     record=self.marc_record)
##	self.assert_(test_redis.exists("bibframe:Annotation:Facet:Access:Online"))
##	self.assert_(test_redis.sismember("bibframe:Annotation:Facet:Access:Online",instance.redis_key))
##
##
##    def test_format_facet(self):
##        instance = Instance(redis=test_redis,
##			    attributes={"rda:carrierTypeManifestation":"Book"})
##	instance.save()
##	self.facet_ingester.add_format_facet(instance=instance)
##	self.assert_(test_redis.exists("bibframe:Annotation:Facet:Format:Book"))
##	self.assert_(test_redis.sismember("bibframe:Annotation:Facet:Format:Book",instance.redis_key))
##
##    def test_lc_facet(self):
##	creative_work = CreativeWork(redis=test_redis)
##	creative_work.save()
##	marc_record = pymarc.Record()
##	marc_record.add_field(pymarc.Field(tag='050',
##		                           indicators=['0','0'],
##					   subfields=['a','QA345','b','T6']))
##        self.facet_ingester.add_lc_facet(creative_work=creative_work,
##			                 record=marc_record)
##	self.assert_(test_redis.exists("bibframe:Annotation:Facet:LOCFirstLetter:QA"))
##	self.assert_(test_redis.sismember("bibframe:Annotation:Facet:LOCFirstLetter:QA",creative_work.redis_key))
##	self.assertEquals(test_redis.hget("bibframe:Annotation:Facet:LOCFirstLetters","QA"),
##                          "QA - Mathematics")
##
##    def test_location_facet(self):
##	instance = Instance(redis=test_redis)
##	instance.save()
##	self.facet_ingester.add_locations_facet(instance=instance,
##			                        record=self.marc_record)
##	self.assert_(test_redis.exists("bibframe:Annotation:Facet:Location:ewwwn"))
##	self.assert_(test_redis.exists("bibframe:Annotation:Facet:Location:tarfc"))
##	self.assert_(test_redis.exists("bibframe:Annotation:Facet:Location:tgr"))
##	self.assertEquals(test_redis.hget("bibframe:Annotation:Facet:Locations","ewwwn"),
##			  "Online")
##	self.assertEquals(test_redis.hget("bibframe:Annotation:Facet:Locations","tarfc"),
##                          "Tutt Reference")
##
##    def tearDown(self):
##        test_redis.flushdb()
##
##
##
class MARC21toInstanceTest(TestCase):

    def setUp(self):
        marc_record = pymarc.Record()
        marc_record.add_field(pymarc.Field(tag='007',
                                           data='c  g a    '))
        marc_record.add_field(pymarc.Field(tag='007',
                                           data='m   a     '))
        marc_record.add_field(pymarc.Field(tag='008',
                                           data='011003s2001        enk300  g       eng         vleng  d'))
        marc_record.add_field(pymarc.Field(tag='010',
                                           indicators=[' ',' '],
                                           subfields=['a','95030619',
                                                      'z','95030619x']))
        marc_record.add_field(pymarc.Field(tag='015',
                                           indicators=[' ',' '],
                                           subfields=['a','B67-25185']))
        marc_record.add_field(pymarc.Field(tag='016',
                                           indicators=[' ',' '],
                                           subfields=['a','890000298']))
        marc_record.add_field(pymarc.Field(tag='017',
                                           indicators=[' ',' '],
                                           subfields=['a','DL 80-0-1524',
                                                      'z','M444120-2006']))
        marc_record.add_field(pymarc.Field(tag='022',
                                           indicators=[' ',' '],
                                           subfields=['a','0264-2875']))
        marc_record.add_field(pymarc.Field(tag='024',
                                           indicators=['0',' '],
                                           subfields=['a','NLC018413261',
                                                      'z','NLC018403261' ]))
        marc_record.add_field(pymarc.Field(tag='024',
                                           indicators=['1',' '],
                                           subfields=['a','7822183031']))
        marc_record.add_field(pymarc.Field(tag='024',
                                           indicators=['2',' '],
                                           subfields=['a','979-0-2600-0043-8']))
        marc_record.add_field(pymarc.Field(tag='024',
                                           indicators=['3',' '],
                                           subfields=['a','9780838934326',
                                                      'd','9000']))

        marc_record.add_field(pymarc.Field(tag='024',
                                           indicators=['4',' '],
                                           subfields=['a','8756-2324(198603/04)65:2L.4:QTP:1-P']))
        marc_record.add_field(pymarc.Field(tag='024',
                                           indicators=['7',' '],
                                           subfields=['a','stdNumber-1224',
                                                      '2','ansi']))
        marc_record.add_field(pymarc.Field(tag='024',
                                           indicators=['7',' '],
                                           subfields=['a','b45647',
                                                      '2','local']))

        marc_record.add_field(pymarc.Field(tag='024',
                                           indicators=['7',' '],
                                           subfields=['a','19200 Baud',
                                                      'z','2400 Baud',
                                                      '2','iso']))
        marc_record.add_field(pymarc.Field(tag='024',
                                           indicators=['7',' '],
                                           subfields=['a','http://www.test.edu/',
                                                      '2','uri']))
        marc_record.add_field(pymarc.Field(tag='024',
                                           indicators=['7',' '],
                                           subfields=['a','56789',
                                                      '2','urn']))
        marc_record.add_field(pymarc.Field(tag='025',
                                           indicators=[' ',' '],
                                           subfields=['a','ET-E-123']))

        marc_record.add_field(pymarc.Field(tag='026',
                                           indicators=[' ',' '],
                                           subfields=['e','dete nkck vess lodo 3 Anno Domini MDCXXXVI 3']))
        marc_record.add_field(pymarc.Field(tag='027',
                                           indicators=[' ',' '],
                                           subfields=['a','FOA--89-40265/C--SE']))
        marc_record.add_field(pymarc.Field(tag='028',
                                           indicators=['0',' '],
                                           subfields=['a','STMA 8007']))

        marc_record.add_field(pymarc.Field(tag='028',
                                           indicators=['2',' '],
                                           subfields=['a','B. & H. 8797']))
        marc_record.add_field(pymarc.Field(tag='028',
                                           indicators=['3',' '],
                                           subfields=['a','L27410X']))
        marc_record.add_field(pymarc.Field(tag='028',
                                           indicators=['4',' '],
                                           subfields=['a','VM600167']))
        marc_record.add_field(pymarc.Field(tag='028',
                                           indicators=['5',' '],
                                           subfields=['a','VA4567']))
        marc_record.add_field(pymarc.Field(tag='030',
                                           indicators=[' ',' '],
                                           subfields=['a','ASIRAF',
                                                      'z','ASITAF']))
        marc_record.add_field(pymarc.Field(tag='035',
                                           indicators=[' ',' '],
                                           subfields=['a','(COCC)S30545600'])) 

        marc_record.add_field(pymarc.Field(tag='036',
                                           indicators=[' ',' '],
                                           subfields=['a','CPS 495441']))
  
        marc_record.add_field(pymarc.Field(tag='037',
                                           indicators=[' ',' '],
                                           subfields=['a','240-951/147']))
        marc_record.add_field(pymarc.Field(tag='050',
                                           indicators=['0','0'],
                                           subfields=['a','QC861.2',
                                                      'b','.B36']))
##        marc_record.add_field(pymarc.Field(tag='086',
##                                           indicators=['0',' '],
##                                           subfields=['a','HE 20.6209:13/45']))
##        marc_record.add_field(pymarc.Field(t	ag='099',
##                                           indicators=[' ',' '],
##                                           subfields=['a','Video 6716']))
        marc_record.add_field(pymarc.Field(tag='300',
                                           indicators=[' ',' '],
                                           subfields=['a','11 v.',
                                                      'b','ill.']))
        marc_record.add_field(pymarc.Field(tag='306',
                                           indicators=[' ',' '],
                                           subfields=['a','014500']))
       

        marc_record.add_field(pymarc.Field(tag='504',
                                           indicators=[' ',' '],
                                           subfields=['a','Literature cited: p. 67-68.',
                                                      'b','19']))
        marc_record.add_field(pymarc.Field(tag='521',
                                           indicators=['2',' '],
                                           subfields=['a','7 & up']))

        marc_record.add_field(pymarc.Field(tag='525',
                                           indicators=[' ',' '],
                                           subfields=['a','Has numerous supplements']))
        marc_record.add_field(pymarc.Field(tag='351',
                                           indicators=[' ',' '],
                                           subfields=['a','Organized into four subgroups',
                                                      'b','Arranged by office of origin',
                                                      'c','Series',
                                                      '3','Records']))
        marc_record.add_field(pymarc.Field(tag='382',
                                           indicators=[' ',' '],
                                           subfields=['a','mixed voices']))
        marc_record.add_field(pymarc.Field(tag='511',
                                           indicators=[' ',' '],
                                           subfields=['a','Cate Blanchett']))

        marc_record.add_field(pymarc.Field(tag='586',
                                           indicators=[' ',' '],
                                           subfields=['a','Book of the Year',
                                                      '3','Certificate']))
        marc_record.add_field(pymarc.Field(tag='856',
                                           indicators=[' ',' '],
                                           subfields=['u','http://hdl.handle.net/10176/coccc:6854']))

##        marc_record.add_field(pymarc.Field(tag='907',
##                                           indicators=[' ',' '],
##                                           subfields=['a','.b1112223x']))
        self.instance_ingester = MARC21toInstance(annotation_ds=test_redis,
                                                  authority_ds=test_redis,
                                                  instance_ds=test_redis,
                                                  marc_record=marc_record,
                                                  creative_work_ds=test_redis)
        self.instance_ingester.ingest()


    def test_init(self):
        self.assert_(self.instance_ingester.instance.redis_key)

    def test_extract_ansi(self):
        self.assertEquals(list(self.instance_ingester.instance.ansi)[0],
                          'stdNumber-1224')

    def test_aspect_ratio(self):
        self.assertEquals(list(self.instance_ingester.instance.aspectRatio)[0],
                          'Standard sound aperture (reduced frame)')

    def test_award_note(self):
        self.assertEquals(list(self.instance_ingester.instance.awardNote)[0],
                          'Certificate Book of the Year')

    def test_extract_coden(self):
        self.assertEquals(list(self.instance_ingester.instance.coden)[0],
                          'ASITAF')
        self.assertEquals(list(self.instance_ingester.instance.coden)[1],
                          'ASIRAF')
        self.assert_(test_redis.sismember('identifiers:CODEN:invalid',
                                          list(self.instance_ingester.instance.coden)[0]))

    def test_extract_color_content(self):
        self.assertEquals(list(self.instance_ingester.instance.colorContent)[0],
                          'Gray scale')

    def test_extract_duration(self):
        self.assertEquals(list(self.instance_ingester.instance.duration)[0],
                          '014500')

    def test_extract_ean(self):
        self.assertEquals(list(self.instance_ingester.instance.ean)[0],
                          '9780838934326-9000')


    def test_fingerprint(self):
        self.assertEquals(list(self.instance_ingester.instance.fingerprint)[0],
                          'dete nkck vess lodo 3 Anno Domini MDCXXXVI 3')

    def test_extract_hdl(self):
        self.assertEquals(list(self.instance_ingester.instance.hdl)[0],
                          'http://hdl.handle.net/10176/coccc:6854')

    def test_extract_illustrative_content_note(self):
        self.assertEquals(list(self.instance_ingester.instance.illustrativeContentNote)[0], 
                          'ill.')

    def test_intended_audience(self):
        self.assertEquals(list(self.instance_ingester.instance.intendedAudience)[0],
                          "Interest grade level 7 & up")
  
    def test_extract_lccn(self):
        self.assertEquals(list(self.instance_ingester.instance.lccn)[0],
                          '95030619')
        self.assertEquals(list(self.instance_ingester.instance.lccn)[1],
                          '95030619x')
        self.assert_(test_redis.sismember('identifiers:lccn:invalid','95030619x'))
 
    def test_extract_issue_number(self):
        self.assertEquals(list(getattr(self.instance_ingester.instance,'issue-number'))[0],
                          'STMA 8007')

    def test_language(self):
        self.assertEquals(list(self.instance_ingester.instance.language)[0],
                          'eng')

    def test_extract_legal_deposit(self):
        self.assertEquals(list(getattr(self.instance_ingester.instance,'legal-deposit'))[0],
                          'DL 80-0-1524')
        self.assert_(test_redis.sismember("identifiers:legal-deposit:invalid",
                                          "M444120-2006"))


    def test_local(self):
        self.assertEquals(list(self.instance_ingester.instance.local)[0],
                          'b45647')
        self.assertEquals(list(self.instance_ingester.instance.local)[0],
                          test_redis.hget(self.instance_ingester.instance.redis_key,
                                          "local"))
##
##    def test_ils_bib_number(self):
##        self.assertEquals(self.instance_ingester.instance.attributes['rda:identifierForTheManifestation']['ils-bib-number'],
##                          'b1112223')
##        self.assertEquals(self.instance_ingester.instance.attributes['rda:identifierForTheManifestation']['ils-bib-number'],
##                          test_redis.hget("{0}:rda:identifierForTheManifestation".format(self.instance_ingester.instance.redis_key),
##                                          'ils-bib-number'))
##
##    def test_sudoc(self):
##        self.assertEquals(self.instance_ingester.instance.attributes['rda:identifierForTheManifestation']['sudoc'],
##                          'HE 20.6209:13/45')
##        self.assertEquals(self.instance_ingester.instance.attributes['rda:identifierForTheManifestation']['sudoc'],
##                          test_redis.hget("{0}:rda:identifierForTheManifestation".format(self.instance_ingester.instance.redis_key),
##                                          "sudoc"))
##
    def test_extract_lc_overseas_acq(self):
        self.assertEquals(list(getattr(self.instance_ingester.instance,'lc-overseas-acq'))[0],
                          test_redis.hget(self.instance_ingester.instance.redis_key,
                                         'lc-overseas-acq'))

    def test_extract_ismn(self):
        self.assertEquals(list(self.instance_ingester.instance.ismn)[0],
                          '979-0-2600-0043-8')
        self.assertEquals(list(self.instance_ingester.instance.ismn)[0],
                          test_redis.hget(self.instance_ingester.instance.redis_key,
                                          'ismn'))

    def test_issn(self):
        self.assertEquals(list(self.instance_ingester.instance.issn)[0],
                         '0264-2875')

    def test_iso(self):
        self.assertEquals(list(self.instance_ingester.instance.iso)[0],
                          '19200 Baud')
        self.assert_(test_redis.sismember('identifiers:iso:invalid','2400 Baud'))

    def test_isrc(self):
        self.assertEquals(list(self.instance_ingester.instance.isrc)[0],
                          'NLC018413261')
        self.assertEquals(list(test_redis.sinter("identifiers:isrc:invalid",
                                                 "{0}:isrc".format(self.instance_ingester.instance.redis_key)))[0],
                          "NLC018403261")

    def test_medium_of_music(self):
        self.assertEquals(list(self.instance_ingester.instance.mediumOfMusic)[0],
                          'mixed voices')

    def test_music_plate(self):
        self.assertEquals(list(getattr(self.instance_ingester.instance,'music-plate'))[0],
                          'B. & H. 8797')
        self.assertEquals(test_redis.hget(self.instance_ingester.instance.redis_key,
                                          'music-plate'),
                         'B. & H. 8797')

    def test_music_publisher(self):
        self.assertEquals(list(getattr(self.instance_ingester.instance,'music-publisher'))[0],
                          'L27410X')


    def test_nban(self):
        self.assertEquals(list(self.instance_ingester.instance.nban)[0],
                          '890000298')

    def test_nbn(self):
        self.assertEquals(list(self.instance_ingester.instance.nbn)[0],
                          'B67-25185')

    def test_organization_system(self):
        self.assertEquals(list(self.instance_ingester.instance.organizationSystem)[0],
                          'Records Organized into four subgroups Arranged by office of origin=Series')

    def test_performer_note(self):
        self.assertEquals(list(self.instance_ingester.instance.performerNote)[0],
                          'Cast: Cate Blanchett')

    def test_publisher_number(self):
        self.assertEquals(list(getattr(self.instance_ingester.instance,
                                       'publisher-number'))[0],
                          'VA4567')


    def test_sici(self):
        self.assertEquals(list(self.instance_ingester.instance.sici)[0],
                          '8756-2324(198603/04)65:2L.4:QTP:1-P')

    def test_sound_content(self):
        self.assertEquals(list(self.instance_ingester.instance.soundContent)[0],
                          'Sound')

    def test_extract_stock_number(self):
        self.assertEquals(list(getattr(self.instance_ingester.instance,'stock-number'))[0],
                          '240-951/147')
        self.assertEquals(list(getattr(self.instance_ingester.instance,'stock-number'))[0],
                          test_redis.hget(self.instance_ingester.instance.redis_key,
                                          "stock-number"))

    def test_extract_strn(self):
        self.assertEquals(list(self.instance_ingester.instance.strn)[0],
                          'FOA--89-40265/C--SE')
 
    def test_study_number(self):
        self.assertEquals(getattr(self.instance_ingester.instance,'study-number'),
                          'CPS 495441') 


    def test_extract_supplementaryContentNote(self):
        self.assertEquals(list(self.instance_ingester.instance.supplementaryContentNote)[0],
                          'Literature cited: p. 67-68. References: 19')
        self.assertEquals(list(test_redis.smembers('{0}:supplementaryContentNote'.format(self.instance_ingester.instance.redis_key)))[1],
                          'Has numerous supplements')

    def test_system_number(self):
        self.assertEquals(list(getattr(self.instance_ingester.instance,'system-number'))[0],
                          '(COCC)S30545600')

    def test_upc(self):
        self.assertEquals(list(self.instance_ingester.instance.upc)[0],
                          '7822183031')


    def test_extract_videorecording_identifier(self):
        self.assertEquals(list(getattr(self.instance_ingester.instance,
                                       'videorecording-identifier'))[0],
                          'VM600167')

    def test_extract_uri(self):
        self.assertEquals(list(self.instance_ingester.instance.uri)[0],
                          'http://www.test.edu/')




    def tearDown(self):
        test_redis.flushdb()


##class MARC21toBIBFRAMETest(TestCase):
##
##    def setUp(self):
##        marc_record = pymarc.Record()
##        marc_record.add_field(pymarc.Field(tag='245',
##                                           indicators=['1','0'],
##                                           subfields=['a','Statistics:',
##                                                      'b','facts or fiction.']))
##        marc_record.add_field(pymarc.Field(tag='050',
##                                           indicators=['0','0'],
##                                           subfields=['a','QC861.2',
##                                                      'b','.B36']))
##        marc_record.add_field(pymarc.Field(tag='907',
##                                           indicators=[' ',' '],
##                                           subfields=['a','.b1112223x']))
##        self.marc21_ingester =  MARC21toBIBFRAME(annotation_ds=test_redis,
##                                                 authority_ds=test_redis,
##                                                 instance_ds=test_redis,
##                                                 marc_record=marc_record,
##                                                 creative_work_ds=test_redis)
##	self.marc21_ingester.ingest()
##
##    def test_init(self):
##        self.assert_(self.marc21_ingester.marc2creative_work.creative_work.redis_key)
##        self.assert_(self.marc21_ingester.marc2instance.instance.redis_key)
##
##    def test_instance_work(self):
##        self.assertEquals(
##            self.marc21_ingester.marc2instance.instance.attributes['bibframe:CreativeWork'],
##            self.marc21_ingester.marc2creative_work.creative_work.redis_key)
##
##    def test_work_instance(self):
##        self.assertEquals(
##            list(self.marc21_ingester.marc2creative_work.creative_work.attributes['bibframe:Instances'])[0],
##            self.marc21_ingester.marc2instance.instance.redis_key)
##
##
##    def tearDown(self):
##        test_redis.flushdb()
##
##
class MARC21toPersonTest(TestCase):

    def setUp(self):
        field100 = pymarc.Field(tag='100',
                                indicators=['1','0'],
                                subfields=['a','Austen, Jane',
                                           'd','1775-1817'])
        self.person_ingester = MARC21toPerson(annotation_ds=test_redis,
                                              authority_ds=test_redis,
                                              field=field100,
                                              instance_ds=test_redis,
                                              creative_work_ds=test_redis)
        self.person_ingester.ingest()

    def test_init(self):
        self.assert_(self.person_ingester.person.redis_key)

    def test_dob(self):
        self.assertEquals(getattr(self.person_ingester.person,'rda:dateOfBirth'),
                          '1775')
        self.assertEquals(getattr(self.person_ingester.person,'rda:dateOfBirth'),
                          test_redis.hget(self.person_ingester.person.redis_key,
                                          'rda:dateOfBirth'))

    def test_dod(self):
        self.assertEquals(getattr(self.person_ingester.person,'rda:dateOfDeath'),
                          '1817')
        self.assertEquals(getattr(self.person_ingester.person,'rda:dateOfDeath'),
                          test_redis.hget(self.person_ingester.person.redis_key,
                                          'rda:dateOfDeath'))

    def test_foaf_givenName(self):
        self.assertEquals(getattr(self.person_ingester.person,'foaf:givenName'),
                          'Jane')
        self.assertEquals(getattr(self.person_ingester.person,'foaf:givenName'),
                          test_redis.hget(self.person_ingester.person.redis_key,
                                          'foaf:givenName'))
        

    def test_preferred_name(self):
        self.assertEquals(self.person_ingester.person.feature('rda:preferredNameForThePerson'),
                          'Austen, Jane')
        self.assertEquals(self.person_ingester.person.feature('rda:preferredNameForThePerson'),
                          test_redis.hget(self.person_ingester.person.redis_key,
                                          'rda:preferredNameForThePerson'))

    def tearDown(self):
        test_redis.flushdb()
##
##class MARC21toSubjectTest(TestCase):
##
##    def setUp(self):
##        field650 = pymarc.Field(tag='650',
##            indicators=['', '0'],
##            subfields=['a', 'Orphans', 'x', 'Fiction'])
##        self.subjects_ingester = MARC21toSubjects(
##            annotation_ds=test_redis,
##            authority_ds=test_redis,
##            creative_work_ds=test_redis,
##            instance_ds=test_redis,
##            field=field650)
##        self.subjects_ingester.ingest()
##        field650_2 = pymarc.Field(tag='650',
##            indicators=['', '0'],
##            subfields=['a', 'Criminals',
##                'x', 'Fiction'])
##        self.subjects_ingester2 = MARC21toSubjects(
##            annotation_ds=test_redis,
##            authority_ds=test_redis,
##            creative_work_ds=test_redis,
##            instance_ds=test_redis,
##            field=field650_2)
##        self.subjects_ingester2.ingest()
##        #marc_record.add_field(
##            #pymarc.Field(tag='651',
##                #indicators=['', '0'],
##                #subfields=['a', 'London (England)',
##                    #'x', 'Fiction']))
##        #marc_record.add_field(
##            #pymarc.Field(tag='655',
##                #indicators=['', '7'],
##                #subfields=['a', 'Bildungsromans.',
##                    #'x', 'Fiction']))
##
##
##    def test_topical_subjects(self):
##        self.assert_(self.subjects_ingester.subjects[0])
##

class MARC21toCreativeWorkTest(TestCase):

    def setUp(self):
        marc_record = pymarc.Record()
        marc_record.add_field(
            pymarc.Field(tag='082',
                indicators=['0',' '],
                subfields=['a','388/.0919']))
        marc_record.add_field(
            pymarc.Field(tag='083',
                indicators=['0',' '],
                subfields=['a','388.13','c','389']))
        marc_record.add_field(
            pymarc.Field(tag='084',
                indicators=[' ',' '],
                subfields=['a','016','a','014']))
        marc_record.add_field(
            pymarc.Field(tag='086',
                indicators=['0',' '],
                subfields=['a', 'A 13.28:F 61/2/981']))
        marc_record.add_field(
            pymarc.Field(tag='245',
                indicators=['1', '0'],
                subfields=['a', 'Statistics:',
                           'b', 'facts or fiction.']))
        marc_record.add_field(
            pymarc.Field(tag='500',
                indicators=[' ',' '],
                subfields=['a', 'Three-dimensional',
                           '3', 'Films, DVDs, and streaming']))
        marc_record.add_field(
            pymarc.Field(tag='511',
                indicators=[' ',' '],
                subfields=['a','Pareto, Vilfredo']))
        marc_record.add_field(
             pymarc.Field(tag='511',
                indicators=[' ',' '],
                subfields=['a','Cutter, Charles']))
        self.work_ingester = MARC21toCreativeWork(annotation_ds=test_redis,
                                                  authority_ds=test_redis,
                                                  instance_ds=test_redis,
                                                  marc_record=marc_record,
                                                  creative_work_ds=test_redis)
        self.work_ingester.ingest()

    def test_init(self):
        self.assert_(self.work_ingester.creative_work.redis_key)

    def test_extract_classification(self):
        self.assertEquals(list(self.work_ingester.creative_work.classification)[1],
                          '016 014')
        self.assertEquals(list(self.work_ingester.creative_work.classification)[0],
                          'A 13.28:F 61/2/981')

    def test_extract_class_ddc(self):
        self.assertEquals(list(getattr(self.work_ingester.creative_work,'class-ddc'))[1],
                          "388/.0919")
        self.assertEquals(list(getattr(self.work_ingester.creative_work,'class-ddc'))[0],
                          "388.13-389")


                         

    def test_extract_note(self):
        self.assertEquals(list(self.work_ingester.creative_work.note)[0],
                          'Films, DVDs, and streaming Three-dimensional')
        self.assertEquals(list(self.work_ingester.creative_work.note)[0],
                          test_redis.hget(self.work_ingester.creative_work.redis_key,'note'))



    def test_extract_performerNote(self):
        self.assertEquals(list(self.work_ingester.creative_work.performerNote)[1],
                          'Cast: Cutter, Charles')
        self.assertEquals(list(self.work_ingester.creative_work.performerNote)[0],
                          'Cast: Pareto, Vilfredo')
        self.assertEquals(self.work_ingester.creative_work.performerNote,
                          test_redis.smembers('{0}:performerNote'.format(self.work_ingester.creative_work.redis_key)))
##
##    def test_metaphone(self):
##        self.assertEquals(
##            self.work_ingester.creative_work.attributes['rda:Title']["phonetic"],
##            "STTSTKSFKTSARFKXN")
##        self.assertEquals(
##            self.work_ingester.creative_work.attributes['rda:Title']["phonetic"],
##            test_redis.hget("{0}:{1}".format(
##                self.work_ingester.creative_work.redis_key,
##                'rda:Title'),
##            "phonetic"))
##
##
##    def test_title(self):
##        self.assertEquals(
##            self.work_ingester.creative_work.attributes['rda:Title']['rda:preferredTitleForTheWork'],
##            'Statistics: facts or fiction.')
##        self.assertEquals(
##            self.work_ingester.creative_work.attributes['rda:Title']['rda:preferredTitleForTheWork'],
##            test_redis.hget("{0}:{1}".format(self.work_ingester.creative_work.redis_key,
##                                                           'rda:Title'),
##                                          'rda:preferredTitleForTheWork'))
##
##    def tearDown(self):
##        test_redis.flushdb()
##
##
##
##class PrideAndPrejudiceMARC21toBIBFRAMETest(TestCase):
##    """
##    The `PrideAndPrejudiceMARC21toBIBFRAMETest`_ uses the 
##    /bibframe/fixures/pride-prejudice.mrc MARC21 record set that includes the following 
##    information about the MARC Records
##
##    Total Records: 19
##    Total Creative Works: 7
##    Total Instances: 19
##    Total Creators: 12
##    """
##
##    def setUp(self):
##        marc_reader = pymarc.MARCReader(open(os.path.join(PROJECT_HOME,
##                                                          'bibframe',
##                                                          'fixures',
##                                                          'pride-and-prejudice.mrc'),
##                                             'rb'))
##        for record in marc_reader:
##            ingester = MARC21toBIBFRAME(annotation_ds=test_redis,
##                                        authority_ds=test_redis,
##                                        instance_ds=test_redis,
##                                        marc_record=record,
##                                        creative_work_ds=test_redis)
##            ingester.ingest()
##              
##
##    def test_authors(self):
##        """
##        Tests total number of expected creators from the MARC21 record set
##        for Pride and Prejudice
##        """
##	self.assertEquals(int(test_redis.get('global bibframe:Authority:Person')),
##	                  12)
##	self.assertEquals(test_redis.hget('bibframe:Authority:Person:3',
##		                          'rda:preferredNameForThePerson'),
##			  'Austen, Jane')
##        for i in range(1,13):
##            author_key = "bibframe:Authority:Person:{0}".format(i)
##            #print(test_redis.hget(author_key,'rda:preferredNameForThePerson'))
##
##	    #print(test_redis.hgetall(author_key))
##            #print(test_redis.smembers("{0}:rda:isCreatorPersonOf".format(author_key)))
##
##    def test_instances(self):
##        """
##	Tests total number of instances from the MARC21 record set for 
##	Pride and Prejudice
##	"""
##	self.assertEquals(int(test_redis.get('global bibframe:Instance')),
##			  19)
##        self.assertEquals(test_redis.hget('bibframe:Instance:1',
##		                          'rda:carrierTypeManifestation'),
##                          'DVD Video')
##        self.assertEquals(test_redis.hget('bibframe:Instance:3',
##		                          'rda:carrierTypeManifestation'),
##                          'Book')
##	for instance_key in list(test_redis.smembers("bibframe:CreativeWork:3:bibframe:Instances")):
##	    pass
##            #self.assertEquals(test_redis.hget(instance_key,
##            #                                  'rda:carrierTypeManifestation'),
##            #                  'book')
##
##    def test_works(self):
##        """
##	Tests total number of works from the MARC21 record set
##        for Pride and Prejudice
##	"""
##	self.assertEquals(int(test_redis.get("global bibframe:CreativeWork")),
##			  7)
##	# bibframe:CreativeWork:3 is the traditional Pride and Prejudice Work 
##	# from Jane Austen
##	self.assertEquals(test_redis.scard("bibframe:CreativeWork:3:bibframe:Instances"),
##			  13)
##	self.assert_(test_redis.sismember("bibframe:CreativeWork:3:rda:creator",
##		                          "bibframe:Authority:Person:3"))
##	for i in range(1,8):
##            cw_key = "bibframe:CreativeWork:{0}".format(i)
##	    #print(test_redis.smembers("{0}:bibframe:Instances".format(cw_key)))
##            #print(test_redis.hgetall("{0}:rda:Title".format(cw_key)))
##
##
##
##
##    def tearDown(self):
##        test_redis.flushdb()
##

class MARC21toLibraryHoldingTest(TestCase):

    def setUp(self):
        marc_record = pymarc.Record()
        marc_record.add_field(pymarc.Field(tag='050',
                                           indicators=[' ',' '],
                                           subfields=['a','PS3602.E267',
                                                      'b','M38 2008']))
        marc_record.add_field(pymarc.Field(tag='082',
                                           indicators=[' ',' '],
                                           subfields = ['a','C848/.5407/05',
                                                        'b','20']))
        marc_record.add_field(pymarc.Field(tag='080',
                                           indicators=[' ',' '],
                                           subfields=['a','631.321:631.411.3']))
        marc_record.add_field(pymarc.Field(tag='086',
                                           indicators=[' ',' '],
                                           subfields=['a','A 1.1:',
                                                      'z','A 1.1/3:984']))

        self.lib_holding_ingester = MARC21toLibraryHolding(annotation_ds=test_redis,
                                                           authority_ds=test_redis,
                                                           instance_ds=test_redis,
                                                           marc_record=marc_record,
                                                           creative_work_ds=test_redis)
        self.lib_holding_ingester.ingest()


    def test_init_(self):
        self.assert_(self.lib_holding_ingester.holding.redis_key is not None)

    def test_extract_ddc(self):
        self.assertEquals(getattr(self.lib_holding_ingester.holding,'callno-ddc'),
                         'C848/.5407/05 20')

    def test_extract_govdoc(self):
        self.assertEquals(getattr(self.lib_holding_ingester.holding,'callno-govdoc'),
                          'A 1.1:')

    def test_extract_lcc(self):
        self.assertEquals(getattr(self.lib_holding_ingester.holding,'callno-lcc'),
                          'PS3602.E267 M38 2008') 

    def test_extract_udc(self):
        self.assertEquals(getattr(self.lib_holding_ingester.holding,'callno-udc'),
                          '631.321:631.411.3') 


    def tearDown(self):
        test_redis.flushdb()


class InstanceTest(TestCase):

    def setUp(self):
        self.holding = Holding(primary_redis=test_redis,
                               annotates=set(["bibframe:Instance:1"]))
        setattr(self.holding,'callno-local','Video 6716')
        setattr(self.holding,'callno-lcc','C1.D11')
        self.holding.save()
        self.existing_redis_key = "bibframe:Instance:{0}".format(test_redis.incr('global bibframe:Instance'))
        test_redis.hset(self.existing_redis_key,
                        'created_on',
                        datetime.datetime.utcnow().isoformat())
        self.instance = Instance(primary_redis=test_redis,
                                 redis_key=self.existing_redis_key,
                                 associatedAgent={'rda:publisher':set(['bibframe:Organization:1'])},
                                 hasAnnotation=set([self.holding.redis_key,]),
                                 instanceOf="bibframe:Work:1")
        self.new_holding = Holding(primary_redis=test_redis)
        setattr(self.new_holding,"callno-sudoc",'HD1695.C7C55 2007')
        self.new_holding.save()
        self.new_instance = Instance(primary_redis=test_redis,
                                     associatedAgent={'rda:publisher':set(['bibframe:Organization:2'])},
                                     hasAnnotation=set([self.new_holding.redis_key,]),
                                     instanceOf="bibframe:Work:2")
        setattr(self.new_instance,'system-number','b1762075')
        self.new_instance.save()
        setattr(self.new_holding,'annotates',set([self.new_instance.redis_key,]))
        self.new_holding.save()

    def test_ils_bib_number(self):
        self.assertEquals(getattr(self.new_instance,'system-number'),
                          test_redis.hget(self.new_instance.redis_key,
                                          "system-number"))

    def test_init(self):
        self.assert_(self.new_instance.primary_redis)
        self.assertEquals(self.new_instance.redis_key,
                          'bibframe:Instance:2')
        self.assert_(self.instance.primary_redis)
        self.assertEquals(self.instance.redis_key,
                          "bibframe:Instance:1")

    def test_lccn_callnumber(self):
        self.assertEquals(list(self.instance.hasAnnotation)[0],
                          self.holding.redis_key)
        self.assertEquals(getattr(self.holding,'callno-lcc'),
                          test_redis.hget(self.holding.redis_key,
                                          'callno-lcc'))
        self.assertEquals(test_redis.hget(list(self.instance.hasAnnotation)[0],
                                          'callno-lcc'),
                          "C1.D11")
        

    def test_local_callnumber(self):
        self.assertEquals(getattr(self.holding,'callno-local'),
                          "Video 6716")
        self.assertEquals(getattr(self.holding,'callno-local'),
                          test_redis.hget(self.holding.redis_key,
                                          'callno-local'))
        self.assertEquals(self.holding.redis_key,
                          list(self.instance.hasAnnotation)[0])
                          

    def test_publisher(self):
        self.assertEquals(list(self.new_instance.associatedAgent['rda:publisher'])[0],
                          'bibframe:Organization:2')
        self.assertEquals(list(self.instance.associatedAgent['rda:publisher'])[0],
                          'bibframe:Organization:1')

    def test_sudoc_callnumber(self):
        self.assertEquals(list(self.new_instance.hasAnnotation)[0],
                          self.new_holding.redis_key)
        self.assertEquals(getattr(self.new_holding,"callno-sudoc"),
                          test_redis.hget(self.new_holding.redis_key,
                                          "callno-sudoc"))
        

    def tearDown(self):
        test_redis.flushdb()

class CreativeWorkTest(TestCase):

    def setUp(self):
        # Test work w/o Redis key (new Work)
        self.new_creative_work = Work(primary_redis=test_redis,
                                      associatedAgent={'rda:isCreatedBy':set(["bibframe:Person:1"])},
                                      languageOfWork="eng",
                                      note=["This is a note for a new creative work",])
        setattr(self.new_creative_work,'rda:dateOfWork',2012)

        self.new_creative_work.save()
        # Tests work w/pre-existing Redis 
	self.existing_key = 'bibframe:Work:2'
        test_redis.hset(self.existing_key,'created','2013-01-07')
        test_redis.hset(self.existing_key,'rda:dateOfWork',1999)
        self.creative_work = Work(primary_redis=test_redis,
                                  redis_key=self.existing_key,
                                  associatedAgent={'rda:isCreatedBy':set(["bibframe:Organization:1"])})
        self.creative_work.save()


    def test_init_(self):
        self.assert_(self.new_creative_work.primary_redis)
        self.assertEquals(self.new_creative_work.redis_key,
                          'bibframe:Work:1')
        self.assert_(self.creative_work.primary_redis)
        self.assertEquals(self.creative_work.redis_key,
                          "bibframe:Work:2")

    def test_dateOfWork(self):
        self.assertEquals(str(getattr(self.new_creative_work,'rda:dateOfWork')),
                          test_redis.hget(self.new_creative_work.redis_key,
                                          "rda:dateOfWork"))
        self.assertEquals(getattr(self.creative_work,'rda:dateOfWork'),
                          test_redis.hget(self.creative_work.redis_key,
                                          'rda:dateOfWork'))

    def test_isCreatedBy(self):
        self.assertEquals(list(self.new_creative_work.associatedAgent['rda:isCreatedBy'])[0],
		          'bibframe:Person:1')
        self.assertEquals(list(self.creative_work.associatedAgent['rda:isCreatedBy'])[0],
                          'bibframe:Organization:1')


    def tearDown(self):
        test_redis.flushdb()


class LibraryHoldingTest(TestCase):

    def setUp(self):
        self.new_holding = Holding(primary_redis=test_redis,
                                   annotates='bibframe:Instance:1')
        setattr(self.new_holding,'callno-lcc','PS3602.E267 M38 2008')
        setattr(self.new_holding,'callno-udc','631.321:631.411.3')
        setattr(self.new_holding,'callno-ddc','388/.0919')
        self.new_holding.save()

    def test_init(self):
        self.assert_(self.new_holding.redis_key is not None)

    def test_annotates(self):
        self.assertEquals(self.new_holding.annotates,
                          'bibframe:Instance:1')
  
    def test_callno_ddc(self):
        self.assertEquals(self.new_holding.feature('callno-ddc'),
                          '388/.0919')

    def test_callno_lcc(self):
        self.assertEquals(self.new_holding.feature('callno-lcc'),
                          'PS3602.E267 M38 2008')

    def test_udc(self):
        self.assertEquals(self.new_holding.feature('callno-udc'),
                          '631.321:631.411.3')



    def tearDown(self):
        test_redis.flushdb()

"""
Tries to import all classifer tests
"""
from bibframe.classifiers.tests import TestWorkClassifier
from bibframe.ingesters.test_ProjectGutenbergRDF import TestProjectGutenbergIngester
