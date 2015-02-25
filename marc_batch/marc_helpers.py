"""
 :mod:`marc_helpers`

"""
import sys,datetime,logging
import urllib.parse
import urllib.request
import re
import os,codecs
import io
from pymarc import Field
import pymarc

UNICODE_CHAR_REPLACEMENT = {
    u'a`': u'\xe0',
    u'O\xa8': u'\xd6',
    u'U\xb4': u'\xda',
    u'e`': u'\xe8',
    u'U\xa8': u'\xdc',
    u'i`': u'\xec',
    u'O\xb4': u'\xd3',
    u'u\xa8': u'\xfc',
    u'E\xa8': u'\xcb',
    u'i^': u'\xee',
    u'u\xb4': u'\xfa',
    u'I\xb4': u'\xcd',
    u'I\xa8': u'\xcf',
    u'e^': u'\xea',
    u'A\xb4': u'\xc1',
    u'n~': u'\xf1',
    u'E\xb4': u'\xc9',
    u'o\xb4': u'\xf3',
    u'a^': u'\xe2',
    u'u^': u'\xfb',
    u'e\xa8': u'\xeb',
    u'I^': u'\xce',
    u'a\xa8': u'\xe4',
    u'i\xb4': u'\xed',
    u'O`': u'\xd2',
    u'o^': u'\xf4',
    u'E^': u'\xca',
    u'a\xb4': u'\xe1',
    u'e\xb4': u'\xe9',
    u'U`': u'\xd9',
    u'A^': u'\xc2',
    u'A`': u'\xc0',
    u'U^': u'\xdb',
    u'i\xa8': u'\xef',
    u'o\xa8': u'\xf6',
    u'E`': u'\xc8',
    u'o`': u'\xf2',
    u'O^': u'\xd4',
    u'c\xb8': u'\xe7',
    u'A\xa8': u'\xc4',
    u'I`': u'\xcc',
    u'u`': u'\xf9',
    u'a\xb0': u'\xe5'}


def clean_unicode(record):
    """Function goes through a MARC record searching for invalid unicode
    characters and replacing with correct character.

    Parameter:
    record -- MARC21 record
    """
    bad_chars = UNICODE_CHAR_REPLACEMENT.keys()
    for field in record.fields:
        for char in bad_chars:
            if unicode(field).find(char) > -1:
                for i, subfield in enumerate(field.subfields):
                    if len(subfield) > 1: # Subfield codes are usually 1 char
                        field.subfields[i] = subfield.replace(
                            char,
                            UNICODE_CHAR_REPLACEMENT.get(char))

    return record



class MARCModifier(object):
    """
    Base class for specific vendor MARC files, children
    classes provide validation methods and methods for adding/
    modifying MARC fields and indicators for import
    """

    def __init__(self,
                 *args):
        if len(args) > 0:
            marc_file_object = args[0]
            if len(args) == 2:
                to_unicode=args[1]
            else:
                to_unicode=True
            self.marc_reader = pymarc.MARCReader(args[0],
                                                 to_unicode=to_unicode)
        self.records = []
        self.stats = {'records':0}

    def decode_fields(self, record):
        "Decodes all fields in the record"
        for field in record.fields:
            for subfield in field.subfields:
                subfield = subfield.decode('utf-8',
                                           errors='ignore')
        return record


    def load(self):
        ''' Method iterates through MARC reader, loads specific MARC records
            from reader.
        '''
        for record in self.marc_reader:
            if record is None:
                break
            raw_record = self.processRecord(record)
            # Removes 009, 509, and 648 fields if they exist
            raw_record = self.remove009(raw_record)
            raw_record = self.remove509(raw_record)
            raw_record = self.remove648(raw_record)
            raw_record.fields = sorted(raw_record.fields,key=lambda x: x.tag)
            self.records.append(raw_record)
            self.stats['records'] += 1



    def processRecord(self,marc_record):
        ''' Method should be overriddden by derived classes.'''
        pass

    def processURLs(self,
                    marc_record,
                    proxy_location,
                    public_note='View online - Access limited to subscribers',
                    note_prefix='Available via Internet'):
        """ Method extracts URL from 856 field, sets 538 and 856 to CC's format practices.

            Parameters:
        :param marc_record: - MARC Record
        :param proxy_location: - proxy prefix prepended to extracted URL from 856 field
        :param public_note: - subfield z value, default is for CC
        :param note_prefix: - prefix for original URL in 538 note field, default is for CC.
        """
        all538fields = marc_record.get_fields('538')
        for field538 in all538fields:
            marc_record.remove_field(field538)
        all856fields = marc_record.get_fields('856')
        for field856 in all856fields:
            # Extracts raw url from 856 subfield u, creates a url object
            # for original and proxy urls and replaces net location with WAM location
            # for proxy
            raw_url = urllib.parse.urlparse(field856.get_subfields('u')[0])
            if re.match(r'http://',proxy_location):
                protocol = ''
            else:
                protocol = 'http://'
            proxy_raw_url = '{}{}{}?{}'.format(protocol,
                                           proxy_location,
                                           raw_url.path,
                                           raw_url.query)
            proxy_url = urllib.parse.urlparse(proxy_raw_url)
            # Sets values for new 538 with constructed note in
            new538 = Field(tag='538',
                           indicators=[' ',' '],
                           subfields=['a','%s, %s' % (note_prefix,raw_url.geturl())])
            marc_record.add_field(new538)
            # Sets values for 856 field
            new856 = Field(tag='856',
                           indicators = ['4','0'],
                           subfields=['u',proxy_url.geturl()])
            # Checks for subfield 3 in original 856 field, adds to public note
            # in subfield z
            new_public_note = public_note
            if len(field856.get_subfields('3')) > 0:
                for subfield3 in field856.get_subfields('3'):
                    subfield3_all = "%s - %s" % (public_note,
                                                 subfield3)
                new_public_note = subfield3_all
            new856.add_subfield('z',new_public_note)
            marc_record.remove_field(field856)
            marc_record.add_field(new856)
        return marc_record


    def output(self):
        "Outputs supporting unicode"
        output_string = cStringIO.StringIO()
        for record in self.records:
            try:
                record_str = record.as_marc()
            except UnicodeEncodeError:
                record.force_utf8 = True
                record_str = record.as_marc()
            try:
                output_string.write(record_str)
            except UnicodeEncodeError:
                output_string.write(record_str.encode('utf8',
                                                      'ignore'))
        return output_string.getvalue()




    def remove009(self,marc_record):
        """
        Removes the 009 field, used in some MARC records for local information
        Not used by CC.

        :param marc_record: MARC record
        """
        return self.__remove_field__(marc_record=marc_record,
                                     tag='009')

    def remove050(self,marc_record):
        """
        Removes the 050 field, used in some MARC records for call number.

        Parameters:
        - `marc_record`: MARC record
        """
        return self.__remove_field__(marc_record=marc_record,
                                     tag='050')

    def remove509(self,marc_record):
        """
        Removes the 509 field, used in some MARC records as a local note.
        Not used by CC.

        Parameters:
        - `marc_record`: MARC record
        """
        return self.__remove_field__(marc_record=marc_record,
                                     tag='509')


    def remove530(self,marc_record):
        """
        Method removes all 530 fields in MARC record

        Parameters:
        `marc_record`: Required, MARC record
        """
        return self.__remove_field__(marc_record=marc_record,
                                     tag='530')

    def remove648(self,marc_record):
        """
        Removes the 648 (Chronological Term) from the MARC record
        Not used by CC.

        Parameters:
        - `marc_record`: MARC record
        """
        return self.__remove_field__(marc_record=marc_record,
                                    tag='648')

    def replace007(self,marc_record,data=None):
        """
        Removes exisiting 007 fields and replaces with standard data
        for the 007 electronic records.

        Parameters:
        - `marc_record`: MARC record
        - `data`: Optional, default data is set if not present
        """
        marc_record = self.__remove_field__(marc_record=marc_record,
                                            tag='007')
        if not data:
            data=r'cr           u'
        new007 = Field(tag='007',data=data)
        marc_record.add_field(new007)
        return marc_record


    def validate006(self,marc_record):
        """
        Default validation of the 006 field with standard
        field data of m||||||||d|||||||| for electronic records.

        Parameters:
        `marc_record`: Required, MARC record
        """
        marc_record = self.__remove_field__(marc_record=marc_record,
                                            tag='006')
        field006 = Field(tag='006',indicators=None)
        field006.data = r'm        d        '
        marc_record.add_field(field006)
        return marc_record

    def validate007(self,marc_record):
        """
        Default validation of the 007 field with the
        standard CC data of cr|||||||||||u

        Parameters:
        `marc_record`: Required, MARC record
        """
        marc_record = self.replace007(marc_record)
        return marc_record

    def validate245(self,marc_record):
        """
        Method adds a subfield 'h' with value of electronic resource
        to the 245 field.

        Parameters:
        `marc_record`: Required, MARC record
        """
        all245s = marc_record.get_fields('245')
        subfield_h_val = '[electronic resource]'
        if len(all245s) > 0:
            field245 = all245s[0]
            marc_record.remove_field(field245)
            subfield_a,subfield_c= '',''
            a_subfields = field245.get_subfields('a')
            indicator1,indicator2 = field245.indicators
            if len(a_subfields) > 0:
                subfield_a = a_subfields[0]
                if len(subfield_a) > 0:
                    if ['.','\\'].count(subfield_a[-1]) > 0:
                        subfield_a = subfield_a[:-1].strip()
            new245 = Field(tag='245',
                           indicators=[indicator1,indicator2],
                           subfields = ['a', u'{0} '.format(subfield_a)])
            b_subfields = field245.get_subfields('b')
            c_subfields = field245.get_subfields('c')
            n_subfields = field245.get_subfields('n')
            p_subfields = field245.get_subfields('p')
            # Order for 245 subfields are:
            # $a $n $p $h $b $c
            if len(n_subfields) > 0:
                 for subfield_n in n_subfields:
                    new245.add_subfield('n', subfield_n)
            if len(p_subfields) > 0:
                 for subfield_p in p_subfields:
                    new245.add_subfield('p', subfield_p)

            if len(c_subfields) > 0 and len(b_subfields) < 1:
                new245.add_subfield('h','{0} / '.format(subfield_h_val))
            elif len(b_subfields) > 0:
                new245.add_subfield('h','{0} : '.format(subfield_h_val))
            else:
                new245.add_subfield('h',subfield_h_val)
            if len(b_subfields) > 0:
                for subfield_b in b_subfields:
                    new245.add_subfield('b',subfield_b)
            if len(c_subfields) > 0:
                for subfield_c in c_subfields:
                    new245.add_subfield('c',subfield_c)
            marc_record.add_field(new245)
        return marc_record

    def validate300(self,marc_record):
        """
        Method removes any existing 300 fields, adds a single
        300 field with default of '1 online resource'.

        Parameters:
        `marc_record`: Required, MARC record
        """
        all300s = marc_record.get_fields('300')
        for field in all300s:
            marc_record.remove_field(field)
        new300 = Field(tag='300',
                       indicators=[' ',' '],
                       subfields=['a','1 online resource'])
        marc_record.add_field(new300)
        return marc_record

    def validate506(self,marc_record):
        """
        Method removes any existing 506 fields, adds a single
        506 field with default of 'Access limited to subscribers.'

        Parameters:
        `marc_record`: Required, MARC record
        """
        all506s = marc_record.get_fields('506')
        for field in all506s:
            marc_record.remove_field(field)
        new506 = Field(tag='506',
                       indicators=[' ',' '],
                       subfields=['a','Access limited to subscribers.'])
        marc_record.add_field(new506)
        return marc_record

    def to_text(self):
        output_string = io.StringIO()
        marc_writer = MARCWriter(output_string)
        for record in self.records:
            marc_writer.write(record)
        return output_string.getvalue()

    def __remove_field__(self,**kwargs):
        """
        Internal method removes all instances of a field in
        the MARC record.

        Parameters:
        `marc_record`: Required, MARC record
        `tag`: Required, tag of field
        """
        if not kwargs.has_key('marc_record') or not kwargs.has_key('tag'):
            raise ValueError('__remove_field__ requires marc_record and tag')
        marc_record,tag = kwargs.get('marc_record'),kwargs.get('tag')
        allfields = marc_record.get_fields(tag)
        for field in allfields:
            marc_record.remove_field(field)
        return marc_record

    def __switch_name__(self,**kwargs):
        """
         Internal method takes a personal name in the format of last_name,
        first_name middle_names and returns the direct form of the personal
        name.

        Parameters:
        `raw_name`: Required, raw name
        `suffix_list`: Optional, default list is JR., SR., I, II, III, IV
        """
        if not kwargs.has_key('raw_name'):
            ValueError("MARCImportBot.__switch_name__ requires a raw_name")
        raw_name = kwargs.get('raw_name')
        if kwargs.has_key('suffix_list'):
            suffix_list = kwargs.get('suffix_list')
        else:
            suffix_list = ['JR','SR','I','II','III','IV',]
        if raw_name[-1].startswith(","):
            raw_name = raw_name[:-1]
        comma_number = raw_name.find(",")
        if comma_number < 1 or comma_number > 1:
            return raw_name
        last_name,rest_of = raw_name.split(",")
        name_fragments = rest_of.lstrip().split(" ")
        name_fragments = ["%s " % i for i in name_fragments]
        last_position = name_fragments[len(name_fragments)-1].upper().strip()
        def test_suffix(i):
            last_position.startswith(i)
        final_name = ''
        if len(filter(test_suffix,suffix_list)) > 0:
            suffix = name_fragments.pop()
            final_name = ''
            for name in name_fragments:
                final_name += "%s " % name
            final_name += "%s %s" % (last_name,suffix)
        else:
            for name in name_fragments:
                final_name += "%s " % name
            final_name += last_name
        return final_name.strip().replace("  "," ")


if __name__ == '__main__':
    print("Colorado College Cataloging Utilities Command Line %s" %\
          datetime.datetime.now().ctime())
