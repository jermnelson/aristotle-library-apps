"""
 :mod:`eapi` -- Classes support manipulating Early American Imprints MARC records to CC's
 standards.
"""
__author__ = 'Jeremy Nelson'

from marc_batch.marc_helpers import MARCModifier
import urlparse
from pymarc import Field

PROXY_LOCATION = ''


class EarlyAmericanImprintsJob(MARCModifier):
    ''' Class reads Early American Imprints MARC file, validates, and
        adds/modifies fields to a new import MARC record for importing
        into TIGER iii database.'''

    def __init__(self,
                 marc_file,
                 **kwargs):
        ''' Creates instance of Early American Imprints process.

        '''
        MARCModifier.__init__(self,marc_file)
	self.field500_stmt = kwargs.get('field500_stmt')
        self.field730_series = kwargs.get('field730_series')

    def processLeader(self,marc_leader):
        ''' 
        Method validates/sets leader positions for MARC record.

        :param marc_leader: MARC file leader
        '''
        # Checks/sets Encoding level in position 17
	new_leader = marc_leader[0:16] + 'L' + marc_leader[17:]
        return new_leader

    def processRecord(self,marc_record): 
        ''' 
        Process MARC Record

        :param marc_record: MARC record 
        ''' 
        #new_leader = self.processLeader(marc_record.leader) 
	#marc_record.leader = None
	#marc_record.leader = new_leader
        marc_record = self.validate001(marc_record) 
        marc_record = self.validate006(marc_record) 
        marc_record = self.validate008(marc_record) 
        marc_record = self.validate049(marc_record)
	marc_record = self.validate245(marc_record)
        marc_record = self.validate260(marc_record)
        marc_record = self.validate300(marc_record)
	marc_record = self.validate500(marc_record)
        marc_record = self.validate506(marc_record)
        marc_record = self.validate530(marc_record)
        marc_record = self.validate533(marc_record)
	marc_record = self.processURLs(marc_record,
			               '0-opac.newsbank.com.tiger.coloradocollege.edu')
        marc_record = self.validate710(marc_record)
        marc_record = self.validate730(marc_record)
        marc_record = self.validate830(marc_record)
	marc_record = self.validate949(marc_record)
        return marc_record 
 
    def validate001(self,marc_record): 
        ''' Method sets 001 Control Number of CC's format. 
 
	:param marc_record -- MARC record 
        ''' 
        field001 = marc_record.get_fields('001')[0] 
        marc_record.remove_field(field001) 
        raw_data = field001.data 
        if raw_data.find('aas') < 0: 
            new_data = "aas{0}".format(raw_data) 
        else: 
            new_data = raw_data 
        field001.data = new_data 
        marc_record.add_field(field001) 
        return marc_record


    def validate006(self,marc_record):
        ''' 
        Method checks/sets 006 fixed length data elements in MARC
        record.

        :param marc_record: MARC record 
        '''
        field006 = Field(tag='006',indicators=None)
        field006.data = r'm     o  d        '
        marc_record.add_field(field006)
        return marc_record

    def validate008(self,marc_record):
        """ 
        Method checks/sets 006 fixed length data elements in MARC
        record.

        :param marc_record: MARC record 
        """
	field008 = marc_record.get_fields('008')[0]
	marc_record = self.__remove_field__(marc_record=marc_record,tag='008')
	field_data_list = []
	for i in field008.data:
            field_data_list.append(i)
	field_data_list[23] = 'o'
	field008.data = ''.join(field_data_list)
	marc_record.add_field(field008)
	return marc_record


    def validate049(self,marc_record):
        ''' 
        Method removes the 049 MARC field from the MARC
        record.

        :param marc_record: MARC record 
        '''
        all_049s = marc_record.get_fields('049')
	for field in all_049s:
            marc_record.remove_field(field)
        return marc_record

    def validate260(self,marc_record):
        """
        Method checks for multiple instances of colons and
        removes all but one.

        :param marc_record: MARC record 
        """
        all260s = marc_record.get_fields('260')
        for field in all260s:
            for subfield in field.get_subfields('a'):
                field.delete_subfield('a')
                if subfield.count(":") > 1:
                    subfield = subfield.replace(":","")
                    subfield = "{0}:".format(subfield)
                field.add_subfield('a',subfield) 
        mixed_subfields = field.subfields
        bracketed_subfields = []
        field.subfields = []
        for i in range(0,len(mixed_subfields)):
            if not i%2:
                bracketed_subfields.append([mixed_subfields[i],
                                            mixed_subfields[i+1]])
        for row in sorted(bracketed_subfields):
            for i in row:
                field.subfields.append(i)        
        return marc_record    
   

    def validate4xx(self,marc_record):
        ''' 
        Method removes the 440/490 MARC fields from the MARC
        record.

        :param marc_record: MARC record 
        '''
        all_4xxs = marc_record.get_fields('440','490')
	for field in all_4xxs:
            marc_record.remove_field(field)
        return marc_record

    def validate500(self,marc_record):
	"""
	Method adds a 500 field to the MARC record

	:param marc_record: MARC21 record
	"""
	new500 = Field(tag='500',
                       indicators=[' ',' '],
                       subfields=['a',self.field500_stmt])
	marc_record.add_field(new500)
	return marc_record


    def validate530(self,marc_record):
	"""
	Method adds a 530 field to the MARC record

	:param marc_record: MARC21 record
	"""
	existing_530s = marc_record.get_fields('530')
	if len(existing_530s) < 1:
	    new530 = Field(tag='530',
                           indicators=[' ',' '],
                           subfields=['a','Microform version available in the Readex Early American Imprints series.'])
	    marc_record.add_field(new530)
	return marc_record

    def validate533(self,marc_record):
	"""
	Method removes subfield n from the 533 field to the MARC record

	:param marc_record: MARC21 record
	"""
	all533s = marc_record.get_fields('533')
	for field in all533s:
	    marc_record.remove_field(field)
	    field.delete_subfield('n')
	    marc_record.add_field(field)
	return marc_record

    def validate710(self,marc_record):
	"""
	Method adds a 710 field to the MARC record

	:param marc_record: MARC21 record
	"""
        new710 = Field(tag='710',
                       indicators=['2',' '],
                       subfields=['a','Readex Microprint Corporation.'])
	marc_record.add_field(new710)
	return marc_record


    def validate730(self,marc_record):
	"""
	Method adds a 730 field to the MARC record

	:param marc_record: MARC21 record
	"""
        new730 = Field(tag='730',
                       indicators=['0',' '],
                       subfields=['a','Early American imprints.',
			          'n',self.field730_series])
	marc_record.add_field(new730)
	return marc_record

    def validate830(self,marc_record):
        """ 
        Method removes the 830 MARC fields from the MARC
        record.

        :param marc_record: MARC record 
        """
	return self.__remove_field__(marc_record=marc_record,
			             tag='830')

    def validate949(self,marc_record):
        """ 
        Method removes the 830 MARC fields from the MARC
        record.

        :param marc_record: MARC record 
        """
	return self.__remove_field__(marc_record=marc_record,
			             tag='949')

