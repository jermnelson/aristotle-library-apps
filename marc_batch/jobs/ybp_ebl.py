"""
 :mod:`ybp_ebl` YBP EBL DDA eBooks Module
"""
from marc_batch.marc_helpers import MARCModifier
from pymarc import Field
import re,logging,copy,codecs,datetime

VOL_RE = re.compile(r"(.*)(vol)[.|\s]*(.*)")
NO_RE = re.compile(r"(.*)([n|N]o)[.|\s]*(.*)")
BD_RE = re.compile(r"(.*)(Ba*n*d)[.|\s]*(.*)")

class ybp_ebl(MARCModifier):
    """
    :class:`ybp_ebl` class takes a YBP EBL DDA MARC record
    file and modifies for import into an ILS
    """

    def __init__(self,marc_file):
        """
        Initializes `ybp_ebl`

        :param marc_file: File location of MARC records
        """
        MARCModifier.__init__(self,marc_file)

    def processRecord(self,
                      marc_record):
        """
        Processes a single MARC record
    
        :param marc_record: Single MARC record 
        """
        marc_record = self.validateLeader(marc_record)
        marc_record = self.validate001(marc_record)
        marc_record = self.validate006(marc_record)
        marc_record = self.validate007s(marc_record)
        marc_record = self.validate008(marc_record)
        marc_record = self.validate040(marc_record)
        marc_record = self.validate050s(marc_record)
        marc_record = self.validate082(marc_record)
        marc_record = self.validate100(marc_record)
        marc_record = self.validate246(marc_record)
        marc_record = self.validate300s(marc_record)
        marc_record = self.validateRDA(marc_record)
        marc_record = self.validateSeries(marc_record)
        marc_record = self.validate506(marc_record)
        marc_record = self.validate538s540(marc_record)
        marc_record = self.validate710(marc_record)
        marc_record = self.validate776(marc_record)
        marc_record = self.validate856(marc_record)
        return marc_record


    def validateLeader(self,
                       marc_record):
        """
        Changes encoding level to 3 in leader position 17

        :param marc_record: MARC record
        """
        leader_list = list(marc_record.leader)
        leader_list[17] = '3'
        leader_list[18] = 'a'
        marc_record.leader = "".join(leader_list)
        return marc_record

    def validate001(self,
                    marc_record):
        """
        Removes prepend in 001

        :param marc_record: MARC record
        """
        field001 = marc_record['001'].value()
        marc_record['001'].value = field001[3:].lower()
        return marc_record

    def validate007s(self,
                     marc_record):
        """
        Validates all 007s in EBL record load

        :param marc_record: Single MARC record 
        """
        return self.replace007(marc_record,
                               data=r'cr  n        a')

    def validate008(self,
                    marc_record):
        """
        Validates all 008 in EBL record load

        :param marc_record: Single MARC record 
        """
        field008_data = marc_record['008'].value()
        marc_record['008'].value = field008_data.replace("o","|") 
        return marc_record

    def validate040(self,
                    marc_record,
                    marc_code='CoCCC'):
        """
        Validates all 040s in EBL record load by adding $d with
        institution MARC code

        :param marc_record: Single MARC record
        :param marc_code: MARC institution code, defaults to CC
        """
        all040s = marc_record.get_fields('040')
        for field040 in all040s:
            field040.add_subfield('d',marc_code)
        return marc_record
        

    def validate050s(self,
                     marc_record):
        """
        Validates all 050s in EBL record load

        :param marc_record: Single MARC record 
        """
        all050s = marc_record.get_fields('050')
        for field050 in all050s:
            first_a = field050.delete_subfield('a')
            other_a = field050.get_subfields('a')
            for counter in range(0,len(other_a)):
                field050.delete_subfield('a')
            field050.add_subfield('a',first_a)
            first_b = field050.delete_subfield('b')
            first_b = subfld_b_process(VOL_RE,first_b,"v.")
            first_b = subfld_b_process(NO_RE,first_b,"no.")
            first_b = subfld_b_process(BD_RE,first_b,"Bd.")
            first_b += 'eb'
            field050.add_subfield('b',first_b)
        return marc_record

    def validate082(self,
                    marc_record):
        """
        Validates the 082 by making sure the indicators are set to 04

        :param marc_record:
        """
        field082s = marc_record.get_fields('082')
        for field082 in field082s:
            field082.indicators = ['0','4']
        return marc_record
            
    def validate100(self,
                    marc_record):
        """
        Validates 100 field in EBL record load 

        :param marc_record: Single MARC record 
        """
        field100 = marc_record['100']
        if field100 is not None:
            marc_record['100'].indicators = ['1',' ']
        return marc_record


    def validate246(self,
                    marc_record):
        """
        Validates 246 field in EBL record load

        :param marc_record: Single MARC record 
        """
        field246 = marc_record['246']
        if field246 is None:
            return marc_record
        return marc_record

    def validate300s(self,
                     marc_record):
        """
        Validates 300 fields in EBL record load

        :param marc_record: Single MARC record 
        """
        all300s = marc_record.get_fields('300')
        for field300 in all300s:
            field300.delete_subfield('a')
            field300.add_subfield('a','1 online resource (1 v.)')
        return marc_record

    def validateRDA(self,
                    marc_record):
        """
        Validates RDA elements in 336, 337, and 338 fields

        :param marc_record: Single MARC record
        """
        # Creates RDA 336 
        self.__remove_field__(marc_record=marc_record,
                              tag='336')
        field336 = Field('336',
                         indicators=[' ',' '],
                         subfields=['a','text',
                                    '2','rdacontent'])
        marc_record.add_field(field336)
        self.__remove_field__(marc_record=marc_record,
                              tag='337')
        field337 = Field('337',
                         indicators=[' ',' '],
                         subfields=['a','computer',
                                    '2','rdamedia'])
        marc_record.add_field(field337)
        self.__remove_field__(marc_record=marc_record,
                              tag='338')
        field338 = Field('338',
                         indicators=[' ',' '],
                         subfields=['a','online resource',
                                    '2','rdamedia'])
        marc_record.add_field(field338)
        return marc_record

    def validateSeries(self,
                       marc_record):
        """
        Validates Series n 440, 490/830 fields 

        :param marc_record: Single MARC record
        """
        if marc_record['490'] is None and marc_record['830'] is None:
            return marc_record
        return marc_record

    def validate506(self,
                    marc_record):
        """
        Validates 506 field

        :param marc_record: Single MARC record
        """
        new506 = Field('506',
                       indicators=[' ',' '],
                       subfields=['a','Access restricted to subscribing institutions. Individual titles purchased upon selection by the 7th affiliated user.'])
        marc_record.add_field(new506)
        return marc_record

    def validate538s540(self,
                        marc_record):
        """
        Adds 538 fields and 540 field

        :param marc_record: Single MARC record
        """
        first538 = Field('538',
                         indicators=[' ',' '],
                         subfields=["a","Book preview interface supplies PDF, image or read-aloud access. Adobe Digital Editions software required for book downloads."])
        marc_record.add_field(first538)
        second538 = Field('538',
                          indicators=[' ',' '],
                          subfields=["a","Users at some libraries may be required to establish a separate no-charge EBL account, and log in to access the full text. For security, do not use a confidential or important ID and password to log in; create a different username and password"])
        marc_record.add_field(second538)
        field540 = Field('540',
                         indicators=[' ',' '],
                         subfields=["a","Books may be viewed online or downloaded (to a maximum of two devices per patron) for personal use only. No derivative use, redistribution or public performance is permitted. Maximum usage allowances -- loan period: 7 days for some publishers;  printing: up to 20% of the total pages;  copy/paste: up to 5% of the total pages."])
        marc_record.add_field(field540)
        return marc_record

    def validate541(self,
                    marc_record):
        """
        Adds a 541 field

        :param marc_record: Single MARC record
        """
        field541 = Field('541',
                         indicators=[' ',' '],
                         subfields=["a","Permanent access license for participating libraries purchased from YBP"])
        marc_record.add_field(field541)
        return marc_record

    def validate710(self,marc_record):
        """Adds a 710 field if missing from marc_record.
       
        :param marc_record: Single MARC record
        """
        if not marc_record['710']:
	    field710 = Field('710',
                             indicators=['2',' '],
                             subfields=["a","Ebooks Corporation"])
            marc_record.add_field(field710)
        return marc_record

        

    def validate776(self,
                    marc_record):
        """
        Validates 776 by insuring indicators are '0' and '8'

        :param marc_record: Single MARC record
        """
        all776s = marc_record.get_fields('776')
        for field776 in all776s:
            new776 = Field(tag='776',
                           indicators = ['0','8'],
                           subfields=field776.subfields)
            marc_record.remove_field(field776)
            marc_record.add_field(new776)
        return marc_record

    def validate856(self,
                    marc_record):
        """
        Validates 856 by changing $z to 'View electronic book'

        :param marc_record: MARC Record
        """
        all856s = marc_record.get_fields('856')
        for field856 in all856s:
            field856.delete_subfield('z')
            field856.add_subfield('z','View electronic book')
        return marc_record

def subfld_b_process(regex,value,repl):
    if value is None:
        return ''
    regex_result = regex.search(value)
    if regex_result is None:
        return value
    b_tuples = list(regex_result.groups())
    b_tuples[1] = regex.sub(repl,b_tuples[1])
    return "".join(b_tuples)
