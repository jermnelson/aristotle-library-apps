"""
 :mod:`springer` -- Classes support manipulating Springer MARC records to CC's
 standards.
"""
__author__ = 'Jeremy Nelson'

import os
from marc_batch.marc_helpers import MARCModifier
import urllib.parse
from pymarc import Field

import re
from rda_enhancement.pcc_conversion import PCCMARCtoRDAConversion

PROXY_LOCATION = 'http://0-www.springerlink.com.tiger.coloradocollege.edu/openurl.asp?genre=book&id=doi:'


class SpringerEBookJob(MARCModifier):
    ''' Class reads SpringLink eBook MARC file, validates, and
        adds/modifies fields to a new import MARC record for importing
        into TIGER iii database.'''

    def __init__(self,
                 marc_file,
                 **kwargs):
        ''' Creates instance of Springer eBook process.

        :param proxy: Optional proxy location, default is PROXY_LOCATION constant
        :param public_note: Optional public note, default is 'View online'
        :param note_prefix: Optional note prefix, default is 'Available via Internet'
        '''
        MARCModifier.__init__(self, marc_file, True)
        self.spr_url = 'http://www.springerlink.com/openurl.asp?genre=book&id=doi:'
        if kwargs.has_key('proxy'):
            self.spr_proxy = kwargs.get('proxy')
        else:
            self.spr_proxy =  PROXY_LOCATION
        if kwargs.has_key('public_note'):
            self.public_note = kwargs.get('public_note')
        else:
            self.public_note = 'View online'
        if kwargs.has_key('note_prefix'):
            self.note_prefix = kwargs.get('note_prefix')
        else:
            self.note_prefix='Available via Internet'


    def processLeader(self,marc_leader):
        '''
        Method validates/sets leader positions for Spring MARC record.

        :param marc_leader: MARC file leader
        '''
        # Checks/sets record type in position 6
        if marc_leader[6-1] != 'a':
            marc_leader = marc_leader[0:5] + 'a' + marc_leader[6:]
        # Checks/sets Encoding level in position 17
        if marc_leader[17-1] != 'u':
            marc_leader = marc_leader[0:16] + 'u' + marc_leader[17:]
        return marc_leader

    def processRecord(self,marc_record):
        '''
        Callback method called by base class load method, Springer
        eBook specific validation.

        :param marc_record: MARC record
        '''
        marc_record.leader = self.processLeader(marc_record.leader)
        marc_record = self.validate001(marc_record)
        marc_record = self.validate006(marc_record)
        marc_record = self.validate008(marc_record)
        marc_record = self.validate245(marc_record)
        marc_record = self.validate300(marc_record)
        marc_record = self.processSpringerURLs(marc_record)
        return marc_record

    def validate001(self,marc_record):
        ''' Method sets 001 Control Number of CC's format.

         :param marc_record: MARC record
            args:
            marc_record -- MARC record
        '''
        field001 = marc_record.get_fields('001')[0]
        marc_record.remove_field(field001)
        raw_data = field001.data
        if raw_data.find('spr') < 0:
            new_data = "spr%s" % raw_data.replace("-","")
        else:
            new_data = raw_data.replace("-","")
        field001.data = new_data
        marc_record.add_field(field001)
        return marc_record


    def validate006(self,marc_record):
        '''
        Method checks/sets 006 fixed length data elements in MARC
        record.

        :param marc_record: MARC record
        '''
        existing_fields = marc_record.get_fields('006')
        if existing_fields:
            field006 = existing_fields[0]
            marc_record.remove_field(field006)
        else:
            field006 = Field(tag='006',indicators=None)
        field006.data = r'm     o  d        '
        marc_record.add_field(field006)
        return marc_record


    def validate008(self,marc_record):
        '''
        Method checks/sets 008 fixed length data elements in MARC
        record.

        :param marc_record: MARC record
        '''
        field008 = marc_record.get_fields('008')[0]
        marc_record.remove_field(field008)
        # Form of item
        if field008.data[24-1] != 's':
            field008.data = field008.data[0:23] + 'o' + field008.data[24:]
        # Nature of content, set to None
        if field008.data[27-1]:
            field008.data = field008.data[0:26] +  r' ' + field008.data[27:]
        marc_record.add_field(field008)
        return marc_record

    def validate245(self, marc_record):
        rda_enhancement = PCCMARCtoRDAConversion(marc_record)
        rda_enhancement.convert245()
        return marc_record

    def validate300(self, marc_record):
        """Method modifies existing 300 field to the following RDA format:

        300  1 online resource (xxvi, 368 pages) : $b illustrations

        Args:
            marc_record(pymarc.Record): Input MARC21

        Returns:
            pymarc.Record: Modified MARC21
        """
        preface_pages_re = re.compile(r"(\w+), (\w+) p+")
        illus_re = re.compile(r"illus")
        all300Fields = marc_record.get_fields('300')
        for field in all300Fields:
            new_a = "1 online resource"
            new300 = Field(tag='300', indicators=[' ',' '])
            subfield_a_lst = field.get_subfields('a')
            if len(subfield_a_lst) < 1:
                new300.add_subfield('a', new_a)
            for subfield in subfield_a_lst:
                illus_search = illus_re.search(subfield)
                preface_search = preface_pages_re.search(subfield)

                if preface_search is not None:
                    preface, pages = preface_search.groups()
                    new_a = "{} ({}, {} pages)".format(
                        new_a,
                        preface.lower(),
                        pages)
                    if illus_search is not None:
                        new_a += " :"
                new300.add_subfield('a', new_a)
                if illus_search is not None:
                    new300.add_subfield('b', 'illustrations')
            marc_record.remove_field(field)
            marc_record.add_field(new300)
        return marc_record

    def processSpringerURLs(self,marc_record):
        '''
        Method overrides parent processURLS for Springer specific
        modification of the 538 and 856 fields

        :param marc_record: MARC record
         '''
        all856fields = marc_record.get_fields('856')
        field856 = all856fields[0]
        for field in all856fields:
            marc_record.remove_field(field)
        raw_url = urllib.parse.urlparse(field856.get_subfields('u')[0])
        doi = raw_url.path[1:]
        all538fields = marc_record.get_fields('538')
        for field in all538fields:
            marc_record.remove_field(field)
        new856 = Field(tag='856',
                       indicators=['4','0'],
                       subfields=['u','%s%s' % (self.spr_proxy,
                                                doi),
                                  'z',self.public_note])
        marc_record.add_field(new856)
        new538 = Field(tag='538',
                       indicators=[" "," "],
                       subfields=['a','%s,%s%s' % (self.note_prefix,
                                                   self.spr_url,
                                                   doi)])
        marc_record.add_field(new538)
        return marc_record

