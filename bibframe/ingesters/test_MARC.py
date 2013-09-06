__author__ = "Jeremy Nelson"
import pymarc
from unittest import TestCase
from aristotle.settings import TEST_REDIS
from bibframe.models import Book
from bibframe.ingesters.MARC21 import *

class TestMARC21RegularExpressions(TestCase):

    def setUp(self):
        pass

    def test_conditional_id(self):
        """Tests MARC matching for such strings as:

        '0247-+2"uri"/a,z'
        """
        result1 = CONDITIONAL_SUBFLD_ID_RE.search('0247-+2"uri"/a,z')
        self.assert_(result1)
        # Subfield 
        self.assertEquals(result1.group('indicator2'),
                          '2')
        # Subfield value
        self.assertEquals(result1.group('fld_value'),
                          'uri')
        result2 = CONDITIONAL_SUBFLD_ID_RE.search('0247-+2"ansi"/a,z')
        self.assertEquals(result2.group('indicator2'),
                          '2')
        self.assertEquals(result2.group('fld_value'),
                          'ansi')

    def test_indicator_conditional(self):
        """Tests MARC matching for conditional indicator strings

        '264 if i2=2 $a+$b+$c'
        'if i1=1, transcribe content of $a'
        """
        result1 = IND_CONDITIONAL_RE.search('264 if i2=2 $a+$b+$c')
        self.assert_(result1)
        self.assertEquals(result1.group('indicator'), '2')
        self.assertEquals(result1.group('test'), '2')
        result2 = IND_CONDITIONAL_RE.search('if i1=1, transcribe content of $a')
        self.assert_(result2)
        self.assertEquals(result2.group('indicator'), '1')
        self.assertEquals(result2.group('test'), '1')
    

    def test_precede(self):
        result1 = PRECEDE_RE.search('508, precede text with "Credits:')
        self.assert_(result1)        
        result2 = PRECEDE_RE.search('504--/a+b(precede info in b with References:')
        self.assert_(result2 is None)

    def test_subfield(self):
        result1 = SUBFLD_RE.findall('020--/a,z')
        self.assert_(result1)
        self.assertEquals(result1[0], 'a')
        self.assertEquals(result1[1], 'z')
        # SUBFLD_RE is meant to run after extracting tags first,
        # matches ,2 in the following string instead of $a
        result2 = SUBFLD_RE.search('130,245,246,247,242,222,210 $a')
        self.assertEquals(result2.group('subfld'),
                          '2')
        result3 = SUBFLD_RE.findall('504--/a+b(precede info in b with References:')
        self.assertEquals(result3[0],
                          'a')

    def test_tags(self):
        result1 = TAGS_RE.findall('130,245,246,247,242,222,210 $a')
        self.assert_(result1)
        self.assertEquals(len(result1), 7)
        self.assertEquals(result1[0],
                          '130')
        self.assertEquals(result1[-1],
                          '210')
        result2 = TAGS_RE.findall('700,710,711, with $t and i2 not 2')
        self.assertEquals(len(result2), 3)
        self.assertEquals(result2, ['700', '710', '711'])

    def tearDown(self):
        pass

class TestMARC21Ingester(TestCase):

    def setUp(self):
        marc_record = pymarc.Record()
        marc_record.add_field(
            pymarc.Field(tag='100',
                         indicators=['0','1'],
                         subfields=['a', 'Austen, Jane',
                                    'd', '1781-1836']),
            pymarc.Field(tag='245',
                         indicators=['1', '0'],
                         subfields=['a', 'Pride and prejudice /',
                                    'c', 'Jane Austen']),
            pymarc.Field(tag='945',
                         indicators=[' ',' '],
                         subfields=['a', 'test_a b12345']))
        self.ingester = MARC21Ingester(redis_datastore=TEST_REDIS,
                                       record=marc_record)
        

    def test_init(self):
        self.assert_(self.ingester is not None)
        self.assertEquals(self.ingester.entity_info,
                          {})

    def test_extract(self):
        value_one = self.ingester.__extract__(tags=['100'],
                                              subfields=['a'])
                                              
        self.assertEquals(value_one,
                          'Austen, Jane')

    def test_rule_one(self):
        rule = '130,245,246,247,242,222,210 $a'
        values_one = self.ingester.__rule_one__(rule)
        self.assertEquals(values_one[0],
                          'Pride and prejudice /')



    def tearDown(self):
        TEST_REDIS.flushdb()
        

class TestMARC21toBIBFRAME(TestCase):

    def setUp(self):
        pass

    def test_duplicate_alliance_marc21(self):
        # Default in test record for the ingestor
        new_record = pymarc.Record()
        new_record.add_field(pymarc.Field(tag='945',
                                          indicators=[' ',' '],
                                          subfields=['a', 'test_a b12345']))
        TEST_REDIS.hset('ils-bib-numbers', 'b12345', 'bf:Work:1')
        ingester = MARC21toBIBFRAME(redis_datastore=TEST_REDIS,
                                    record=new_record)
        self.assert_(ingester.__duplicate_check__('ils-bib-numbers') is True)

    def test_duplicate_cc_marc21(self):
        # Default in test for Colorado College specific ingestor
        record = pymarc.Record()
        record.add_field(pymarc.Field(tag='907',
                                      indicators=[' ',' '],
                                      subfields=['a', '.b12345x']))
        TEST_REDIS.hset('ils-bib-numbers', 'b12345', 'bf:Work:1')
        ingester = MARC21toBIBFRAME(redis_datastore=TEST_REDIS,
                                    record=record)
        self.assert_(ingester.__duplicate_check__('ils-bib-numbers') is True)

    def tearDown(self):
        TEST_REDIS.flushdb()
        

class TestMARC21toCreativeWork(TestCase):

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
        self.work_ingester = MARC21toCreativeWork(redis_datastore=TEST_REDIS,
                                                  record=marc_record)
        self.work_ingester.ingest()

    def test_init(self):
        self.assert_(self.work_ingester.creative_work.redis_key)

    def test_classify_work_class(self):
        book_rec = pymarc.Record()
        book_rec.leader = '      a   '
        book_ingester = MARC21toCreativeWork(redis_datastore=TEST_REDIS,
                                             record=book_rec)
        book_ingester.__classify_work_class__()
        self.assertEquals(book_ingester.work_class,
                          Book)

    def test_extract_classification(self):
        classifications = getattr(self.work_ingester.creative_work,
                                  'class')
        self.assertEquals(list(classifications)[0],
                          '014 016')
##        self.assertEquals(list(classifications)[0],                                       
##                          'A 13.28:F 61/2/981')

    def test_extract_class_ddc(self):
        self.assertEquals(list(getattr(self.work_ingester.creative_work,
                                       'class-ddc'))[0],
                          "388/.0919")
##        self.assertEquals(list(getattr(self.work_ingester.creative_work,
##                                       'class-ddc'))[0],
##                          "388.13-389")


                         

    def test_extract_note(self):
        self.assertEquals(list(self.work_ingester.creative_work.note)[0],
                          'Films, DVDs, and streaming Three-dimensional')
##        self.assertEquals(list(self.work_ingester.creative_work.note)[0],
##                          TEST_REDIS.hget(self.work_ingester.creative_work.redis_key,
##                                          'note'))



    def test_extract_performerNote(self):
        self.assertEquals(list(self.work_ingester.creative_work.performerNote)[1],
                          'Cast: Cutter, Charles')
        self.assertEquals(list(self.work_ingester.creative_work.performerNote)[0],
                          'Cast: Pareto, Vilfredo')
        self.assertEquals(self.work_ingester.creative_work.performerNote,
                          TEST_REDIS.smembers('{0}:performerNote'.format(self.work_ingester.creative_work.redis_key)))

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
                                           indicators=['0','0'],
                                           subfields=['a','STMA 8007']))

        marc_record.add_field(pymarc.Field(tag='028',
                                           indicators=['2','0'],
                                           subfields=['a','B. & H. 8797']))
        marc_record.add_field(pymarc.Field(tag='028',
                                           indicators=['3','0'],
                                           subfields=['a','L27410X']))
        marc_record.add_field(pymarc.Field(tag='028',
                                           indicators=['4','0'],
                                           subfields=['a','VM600167']))
        marc_record.add_field(pymarc.Field(tag='028',
                                           indicators=['5','1'],
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
                                           indicators=['1',' '],
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
        self.instance_ingester = MARC21toInstance(redis_datastore=TEST_REDIS,
                                                  record=marc_record)
                                                  
        self.instance_ingester.ingest()


    def test_init(self):
        self.assert_(self.instance_ingester.instance.redis_key)

    def test_extract_ansi(self):
        self.assertEquals(self.instance_ingester.instance.ansi,
                          ['stdNumber-1224'])

    def test_aspect_ratio(self):
        self.assertEquals(self.instance_ingester.instance.aspectRatio,
                          ['Standard sound aperture (reduced frame)'])

    def test_award_note(self):
        self.assertEquals(self.instance_ingester.instance.awardNote,
                          ['Certificate Book of the Year'])

    def test_extract_coden(self):
        self.assertEquals(self.instance_ingester.instance.coden[0],
                          'ASIRAF')
        self.assertEquals(self.instance_ingester.instance.coden[1],
                          'ASITAF')
        self.assert_(TEST_REDIS.sismember('identifiers:coden:invalid',
                                          self.instance_ingester.instance.coden[1]))

    def test_extract_color_content(self):
        
        self.assertEquals(self.instance_ingester.instance.colorContent,
                          ['Gray scale'])

    def test_extract_duration(self):
        self.assertEquals(self.instance_ingester.instance.duration,
                          ['014500'])

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
        self.assert_(TEST_REDIS.sismember('identifiers:lccn:invalid','95030619x'))
 
    def test_extract_issue_number(self):
        self.assertEquals(list(getattr(self.instance_ingester.instance,'issue-number'))[0],
                          'STMA 8007')

    def test_language(self):
        self.assertEquals(self.instance_ingester.instance.language,
                          'English')

    def test_extract_legal_deposit(self):
        self.assertEquals(list(getattr(self.instance_ingester.instance,'legal-deposit'))[0],
                          'DL 80-0-1524')
        self.assert_(TEST_REDIS.sismember("identifiers:legal-deposit:invalid",
                                          "M444120-2006"))


    def test_local(self):
        self.assertEquals(list(self.instance_ingester.instance.local)[0],
                          'b45647')
        self.assertEquals(list(self.instance_ingester.instance.local)[0],
                          TEST_REDIS.hget(self.instance_ingester.instance.redis_key,
                                          "local"))

##    def test_ils_bib_number(self):
##        self.assertEquals(self.instance_ingester.instance.attributes['rda:identifierForTheManifestation']['ils-bib-number'],
##                          'b1112223')
##        self.assertEquals(self.instance_ingester.instance.attributes['rda:identifierForTheManifestation']['ils-bib-number'],
##                          TEST_REDIS.hget("{0}:rda:identifierForTheManifestation".format(self.instance_ingester.instance.redis_key),
##                                          'ils-bib-number'))

    def test_extract_lc_overseas_acq(self):
        self.assertEquals(list(getattr(self.instance_ingester.instance,'lc-overseas-acq'))[0],
                          TEST_REDIS.hget(self.instance_ingester.instance.redis_key,
                                         'lc-overseas-acq'))

    def test_extract_ismn(self):
        self.assertEquals(list(self.instance_ingester.instance.ismn)[0],
                          '979-0-2600-0043-8')
        self.assertEquals(list(self.instance_ingester.instance.ismn)[0],
                          TEST_REDIS.hget(self.instance_ingester.instance.redis_key,
                                          'ismn'))

    def test_issn(self):
        self.assertEquals(list(self.instance_ingester.instance.issn)[0],
                         '0264-2875')

    def test_iso(self):
        self.assertEquals(list(self.instance_ingester.instance.iso)[0],
                          '19200 Baud')
        self.assert_(TEST_REDIS.sismember('identifiers:iso:invalid','2400 Baud'))

    def test_isrc(self):
        self.assertEquals(self.instance_ingester.instance.isrc,
                          ['NLC018413261'])
        self.assertEquals(list(TEST_REDIS.sinter("identifiers:isrc:invalid",
                                                 "{0}:isrc".format(self.instance_ingester.instance.redis_key))),
                          ["NLC018403261"])

    def test_medium_of_music(self):
        self.assertEquals(self.instance_ingester.instance.mediumOfMusic,
                          ['mixed voices'])

    def test_music_plate(self):
        self.assertEquals(list(getattr(self.instance_ingester.instance,'music-plate'))[0],
                          'B. & H. 8797')
        self.assertEquals(TEST_REDIS.hget(self.instance_ingester.instance.redis_key,
                                          'music-plate'),
                         'B. & H. 8797')

    def test_music_publisher(self):
        self.assertEquals(getattr(self.instance_ingester.instance,
                                  'music-publisher'),
                          ['L27410X'])


    def test_nban(self):
        self.assertEquals(self.instance_ingester.instance.nban,
                          ['890000298'])

    def test_nbn(self):
        self.assertEquals(self.instance_ingester.instance.nbn,
                          ['B67-25185'])

    def test_organization_system(self):
        self.assertEquals(self.instance_ingester.instance.organizationSystem,
                          ['Records Organized into four subgroups Arranged by office of origin=Series'])

    def test_performer_note(self):
        self.assertEquals(self.instance_ingester.instance.performerNote,
                          ['Cast: Cate Blanchett'])

    def test_publisher_number(self):
        self.assertEquals(getattr(self.instance_ingester.instance,
                                  'publisher-number'),
                          ['VA4567'])


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
                          TEST_REDIS.hget(self.instance_ingester.instance.redis_key,
                                          "stock-number"))

    def test_extract_strn(self):
        self.assertEquals(list(self.instance_ingester.instance.strn)[0],
                          'FOA--89-40265/C--SE')
 
    def test_study_number(self):
        self.assertEquals(getattr(self.instance_ingester.instance,
                                  'study-number'),
                          ['CPS 495441']) 


    def test_extract_supplementaryContentNote(self):
        self.assertEquals(list(self.instance_ingester.instance.supplementaryContentNote)[0],
                          'Literature cited: p. 67-68. References: 19')
        self.assertEquals(list(TEST_REDIS.smembers('{0}:supplementaryContentNote'.format(self.instance_ingester.instance.redis_key)))[1],
                          'Has numerous supplements')

    def test_system_number(self):
        self.assertEquals(getattr(self.instance_ingester.instance,'system-number'),
                          ['(COCC)S30545600'])

    def test_upc(self):
        self.assertEquals(self.instance_ingester.instance.upc,
                          ['7822183031'])


    def test_extract_videorecording_identifier(self):
        self.assertEquals(getattr(self.instance_ingester.instance,
                                  'videorecording-identifier'),
                          ['VM600167'])

    def test_extract_uri(self):
        self.assertEquals(self.instance_ingester.instance.uri,
                          ['http://www.test.edu/'])
        
    def tearDown(self):
        TEST_REDIS.flushdb()


class TestMARC21toLibraryHolding(TestCase):

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
                                                      'z','A 1.1/3:984']),
                              pymarc.Field(tag='945',
                                           indicators=[' ',' '],
                                           subfields=['a','xwer b12345 i4567']))

        self.lib_holding_ingester = MARC21toLibraryHolding(redis_datastore=TEST_REDIS,
                                                           record=marc_record,
                                                           local=False)
        self.lib_holding_ingester.ingest()


    def test_init_(self):
        self.assert_(self.lib_holding_ingester.holdings[0].redis_key is not None)

    def test_extract_ddc(self):
        self.assertEquals(getattr(self.lib_holding_ingester.holdings[0],
                                  'callno-ddc'),
                         'C848/.5407/05 20')

    def test_extract_govdoc(self):
        self.assertEquals(getattr(self.lib_holding_ingester.holdings[0],
                                  'callno-govdoc'),
                          'A 1.1:')

    def test_extract_lcc(self):
        self.assertEquals(getattr(self.lib_holding_ingester.holdings[0],
                                  'callno-lcc'),
                          'PS3602.E267 M38 2008') 

    def test_extract_udc(self):
        self.assertEquals(getattr(self.lib_holding_ingester.holdings[0],
                                  'callno-udc'),
                          '631.321:631.411.3') 


    def tearDown(self):
        TEST_REDIS.flushdb()

class TestMARC21toPerson(TestCase):

    def setUp(self):
        self.marc_field = pymarc.Field(
                tag='100',
                indicators=['1','0'],
                subfields=['a','Austen, Jane',
                           'd','1775-1817'])
        self.person_ingester = MARC21toPerson(field=self.marc_field,
                                              redis_datastore=TEST_REDIS)
                                              
        self.person_ingester.ingest()

    def test_init(self):
        self.assert_(self.person_ingester.person.redis_key)

    def test_dob(self):
        self.assertEquals(getattr(self.person_ingester.person,
                                  'rda:dateOfBirth'),
                          '1775')
        self.assertEquals(getattr(self.person_ingester.person,
                                  'rda:dateOfBirth'),
                          TEST_REDIS.hget(self.person_ingester.person.redis_key,
                                          'rda:dateOfBirth'))

    def test_dod(self):
        self.assertEquals(getattr(self.person_ingester.person,
                                  'rda:dateOfDeath'),
                          '1817')
        self.assertEquals(getattr(self.person_ingester.person,
                                  'rda:dateOfDeath'),
                          TEST_REDIS.hget(self.person_ingester.person.redis_key,
                                          'rda:dateOfDeath'))

    def test_schema_givenName(self):
        self.assertEquals(getattr(self.person_ingester.person,'schema:givenName'),
                          'Jane')
        self.assertEquals(getattr(self.person_ingester.person,
                                  'schema:givenName'),
                          TEST_REDIS.hget(self.person_ingester.person.redis_key,
                                          'schema:givenName'))
        

    def test_preferred_name(self):
        self.assertEquals(self.person_ingester.person.feature('rda:preferredNameForThePerson'),
                          'Austen, Jane')
        self.assertEquals(self.person_ingester.person.feature('rda:preferredNameForThePerson'),
                          TEST_REDIS.hget(self.person_ingester.person.redis_key,
                                          'rda:preferredNameForThePerson'))

    def tearDown(self):
        TEST_REDIS.flushdb()

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
##	self.facet_ingester = MARC21toFacets(annotation_ds=TEST_REDIS,
##			                     authority_ds=TEST_REDIS,
##					     instance_ds=TEST_REDIS,
##					     creative_work_ds=TEST_REDIS,
##					     marc_record=self.marc_record)
##
##    def test_access_facet(self):
##	instance = Instance(redis=TEST_REDIS)
##	instance.save()
##	self.facet_ingester.add_access_facet(instance=instance,
##			                     record=self.marc_record)
##	self.assert_(TEST_REDIS.exists("bibframe:Annotation:Facet:Access:Online"))
##	self.assert_(TEST_REDIS.sismember("bibframe:Annotation:Facet:Access:Online",instance.redis_key))
##
##
##    def test_format_facet(self):
##        instance = Instance(redis=TEST_REDIS,
##			    attributes={"rda:carrierTypeManifestation":"Book"})
##	instance.save()
##	self.facet_ingester.add_format_facet(instance=instance)
##	self.assert_(TEST_REDIS.exists("bibframe:Annotation:Facet:Format:Book"))
##	self.assert_(TEST_REDIS.sismember("bibframe:Annotation:Facet:Format:Book",instance.redis_key))
##
##    def test_lc_facet(self):
##	creative_work = CreativeWork(redis=TEST_REDIS)
##	creative_work.save()
##	marc_record = pymarc.Record()
##	marc_record.add_field(pymarc.Field(tag='050',
##		                           indicators=['0','0'],
##					   subfields=['a','QA345','b','T6']))
##        self.facet_ingester.add_lc_facet(creative_work=creative_work,
##			                 record=marc_record)
##	self.assert_(TEST_REDIS.exists("bibframe:Annotation:Facet:LOCFirstLetter:QA"))
##	self.assert_(TEST_REDIS.sismember("bibframe:Annotation:Facet:LOCFirstLetter:QA",creative_work.redis_key))
##	self.assertEquals(TEST_REDIS.hget("bibframe:Annotation:Facet:LOCFirstLetters","QA"),
##                          "QA - Mathematics")
##
##    def test_location_facet(self):
##	instance = Instance(redis=TEST_REDIS)
##	instance.save()
##	self.facet_ingester.add_locations_facet(instance=instance,
##			                        record=self.marc_record)
##	self.assert_(TEST_REDIS.exists("bibframe:Annotation:Facet:Location:ewwwn"))
##	self.assert_(TEST_REDIS.exists("bibframe:Annotation:Facet:Location:tarfc"))
##	self.assert_(TEST_REDIS.exists("bibframe:Annotation:Facet:Location:tgr"))
##	self.assertEquals(TEST_REDIS.hget("bibframe:Annotation:Facet:Locations","ewwwn"),
##			  "Online")
##	self.assertEquals(TEST_REDIS.hget("bibframe:Annotation:Facet:Locations","tarfc"),
##                          "Tutt Reference")
##
##    def tearDown(self):
##        TEST_REDIS.flushdb()
##
##
##


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
##        self.marc21_ingester =  MARC21toBIBFRAME(annotation_ds=TEST_REDIS,
##                                                 authority_ds=TEST_REDIS,
##                                                 instance_ds=TEST_REDIS,
##                                                 marc_record=marc_record,
##                                                 creative_work_ds=TEST_REDIS)
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
##        TEST_REDIS.flushdb()
##
##

##
##class MARC21toSubjectTest(TestCase):
##
##    def setUp(self):
##        field650 = pymarc.Field(tag='650',
##            indicators=['', '0'],
##            subfields=['a', 'Orphans', 'x', 'Fiction'])
##        self.subjects_ingester = MARC21toSubjects(
##            annotation_ds=TEST_REDIS,
##            authority_ds=TEST_REDIS,
##            creative_work_ds=TEST_REDIS,
##            instance_ds=TEST_REDIS,
##            field=field650)
##        self.subjects_ingester.ingest()
##        field650_2 = pymarc.Field(tag='650',
##            indicators=['', '0'],
##            subfields=['a', 'Criminals',
##                'x', 'Fiction'])
##        self.subjects_ingester2 = MARC21toSubjects(
##            annotation_ds=TEST_REDIS,
##            authority_ds=TEST_REDIS,
##            creative_work_ds=TEST_REDIS,
##            instance_ds=TEST_REDIS,
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


##
##    def test_metaphone(self):
##        self.assertEquals(
##            self.work_ingester.creative_work.attributes['rda:Title']["phonetic"],
##            "STTSTKSFKTSARFKXN")
##        self.assertEquals(
##            self.work_ingester.creative_work.attributes['rda:Title']["phonetic"],
##            TEST_REDIS.hget("{0}:{1}".format(
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
##            TEST_REDIS.hget("{0}:{1}".format(self.work_ingester.creative_work.redis_key,
##                                                           'rda:Title'),
##                                          'rda:preferredTitleForTheWork'))
##
##    def tearDown(self):
##        TEST_REDIS.flushdb()
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
##            ingester = MARC21toBIBFRAME(annotation_ds=TEST_REDIS,
##                                        authority_ds=TEST_REDIS,
##                                        instance_ds=TEST_REDIS,
##                                        marc_record=record,
##                                        creative_work_ds=TEST_REDIS)
##            ingester.ingest()
##              
##
##    def test_authors(self):
##        """
##        Tests total number of expected creators from the MARC21 record set
##        for Pride and Prejudice
##        """
##	self.assertEquals(int(TEST_REDIS.get('global bibframe:Authority:Person')),
##	                  12)
##	self.assertEquals(TEST_REDIS.hget('bibframe:Authority:Person:3',
##		                          'rda:preferredNameForThePerson'),
##			  'Austen, Jane')
##        for i in range(1,13):
##            author_key = "bibframe:Authority:Person:{0}".format(i)
##            #print(TEST_REDIS.hget(author_key,'rda:preferredNameForThePerson'))
##
##	    #print(TEST_REDIS.hgetall(author_key))
##            #print(TEST_REDIS.smembers("{0}:rda:isCreatorPersonOf".format(author_key)))
##
##    def test_instances(self):
##        """
##	Tests total number of instances from the MARC21 record set for 
##	Pride and Prejudice
##	"""
##	self.assertEquals(int(TEST_REDIS.get('global bibframe:Instance')),
##			  19)
##        self.assertEquals(TEST_REDIS.hget('bibframe:Instance:1',
##		                          'rda:carrierTypeManifestation'),
##                          'DVD Video')
##        self.assertEquals(TEST_REDIS.hget('bibframe:Instance:3',
##		                          'rda:carrierTypeManifestation'),
##                          'Book')
##	for instance_key in list(TEST_REDIS.smembers("bibframe:CreativeWork:3:bibframe:Instances")):
##	    pass
##            #self.assertEquals(TEST_REDIS.hget(instance_key,
##            #                                  'rda:carrierTypeManifestation'),
##            #                  'book')
##
##    def test_works(self):
##        """
##	Tests total number of works from the MARC21 record set
##        for Pride and Prejudice
##	"""
##	self.assertEquals(int(TEST_REDIS.get("global bibframe:CreativeWork")),
##			  7)
##	# bibframe:CreativeWork:3 is the traditional Pride and Prejudice Work 
##	# from Jane Austen
##	self.assertEquals(TEST_REDIS.scard("bibframe:CreativeWork:3:bibframe:Instances"),
##			  13)
##	self.assert_(TEST_REDIS.sismember("bibframe:CreativeWork:3:rda:creator",
##		                          "bibframe:Authority:Person:3"))
##	for i in range(1,8):
##            cw_key = "bibframe:CreativeWork:{0}".format(i)
##	    #print(TEST_REDIS.smembers("{0}:bibframe:Instances".format(cw_key)))
##            #print(TEST_REDIS.hgetall("{0}:rda:Title".format(cw_key)))
##
##
##
##
##    def tearDown(self):
##        TEST_REDIS.flushdb()
##
        
