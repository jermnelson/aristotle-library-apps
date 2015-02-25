"""
 :mod:`aps_base` Base classes and function for manipulating Alexander Street
 Press MARC21 record loads to CC's standards
"""
__author__ = "Jeremy Nelson"


import urllib.parse as urlparse
import urllib.request

import re
import datetime
import logging
from marc_batch.marc_helpers import MARCModifier
from pymarc import Field


class AlexanderStreetPressBase(MARCModifier):
    """
    `AlexanderStreetPressBase` encapsulates the basic
    MARC record changes used by child classes.
    """

    def __init__(self, marc_file, **kwargs):
        """
        Creates instance of `AlexanderStreetPressBase`


        :param marc_file: Alexander Street Press MARC records
        :param asp_code: Alexander Street Press Code, default is asp
        """
        MARCModifier.__init__(self, marc_file, True)
        if not kwargs.has_key('asp_code'):
            self.asp_code = 'asp'
        else:
            self.asp_code = kwargs.get('asp_code')
        self.resolved_baseurl = None

    def getResolvedURL(self,
                       marc_record):
        """
        Method extract's base resolved url from marc_record, sets
        class variable for further processing.

        Parameters:
        - `marc_record`: MARC record, required
        """
        field856 = marc_record.get_fields('856')[0]
        raw_url = field856.get_subfields('u')[0]
        redirect = urllib.request.urlopen(raw_url)
        redirect_url = urllib.parse.urlparse(redirect.geturl())
        query_prefix = redirect_url.query.split("=")[0]
        self.resolved_baseurl = "{0}://{1}{2}?{3}".format(redirect_url.scheme,
                                                          redirect_url.netloc,
                                                          redirect_url.path,
                                                          query_prefix)

    def remove440(self,marc_record):
        """
        Method removes 440 Series Statement field.

        Parameters:
        - `marc_record`: MARC record, required
        """
        return self.__remove_field__(marc_record=marc_record,
                                     tag='440')


    def remove490(self,marc_record):
        """
        Method removes 490 Series Statement field.

        Parameters:
        - `marc_record`: MARC record, required
        """
        return self.__remove_field__(marc_record=marc_record,
                                     tag='490')

    def remove830(self,marc_record):
        """
        Method removes MARC 830 field

        Parameters:
        - `marc_record`: MARC record, required
        """
        return self.__remove_field__(marc_record=marc_record,
                                     tag='830')

    def validate506(self,marc_record):
        """
        Method adds 506 field

        Parameters:
        - `marc_record`: MARC record, required
        """
        marc_record = self.__remove_field__(marc_record=marc_record,
                                            tag='506')
        new506 = Field(tag='506',
                       indicators=[' ',' '],
                       subfields=['a','Access limited to subscribers.'])
        marc_record.add_field(new506)
        return marc_record

    def validate533(self,marc_record):
        """
        Method removes subfield n if exists in field 533

        Parameters:
        - `marc_record`: MARC record, required
        """
        all533fields = marc_record.get_fields('533')
        for field in all533fields:
            marc_record.remove_field(field)
            field.delete_subfield('n')
            marc_record.add_field(field)
        return marc_record

    def validate710(self,marc_record):
        """
        Method adds MARC 710 field, Corporate Heading

        Parameters:
        - `marc_record`: MARC Record, required
        """
        new710field = Field(tag='710',
                            indicators=['2',' '],
                            subfields=['a','Alexander Street Press.'])
        marc_record.add_field(new710field)
        return marc_record

    def validate730(self,
                    marc_record,
                    uniform_title):
        """
        Methods adds MARC 730 field, Added entry: uniform title

        Parameters:
        - `marc_record`: MARC record, required
        - `uniform_title`: Uniform title, required
        """
        new730field = Field(tag='730',
                            indicators=['0',' '],
                            subfields=['a',uniform_title])
        marc_record.add_field(new730field)
        return marc_record

    def validateURLs(self,
                     marc_record,
                     proxy_location,
                     public_note=None):
        """
        Method retrieves URL from 856 field, retrieves redirected
        url and sets new value to existing 856, calls processURLs
        method and returns result

        Parameters:
        - `marc_record`: MARC record, required
        - `proxy_location`: Proxy location, required
        """
        all856s = marc_record.get_fields('856')
        for field856 in all856s:
            raw_url = urlparse.urlparse(field856.get_subfields('u')[0])
            record_id = raw_url.query.split(";")[1]
            new_url = "{0}={1}".format(self.resolved_baseurl,record_id)
            field856.delete_subfield('u')
            field856.add_subfield('u',new_url)
        if public_note:
            return self.processURLs(marc_record=marc_record,
                                    proxy_location=proxy_location,
                                    public_note=public_note)
        return self.processURLs(marc_record=marc_record,
                                proxy_location=proxy_location)


class AlexanderStreetPressMusicJob(AlexanderStreetPressBase):
    """
    The `AlexanderStreetPressMusicJob` is the base class for
    Alexander Street Press jobs.
    """
    DATABASES = {'American song':{'code':'amso',
                                           'proxy':'0-amso.alexanderstreet.com.tiger.coloradocollege.edu'},
                 'Classical music library':{'code':'clmu',
                                            'proxy':'0-clmu.alexanderstreet.com.tiger.coloradocollege.edu'},
                 'Contemporary world music':{'code':'womu',
                                             'proxy':'0-womu.alexanderstreet.com.tiger.coloradocollege.edu'},
                 'Jazz music library':{'code':'jazz',
                                       'proxy':'0-jazz.alexanderstreet.com.tiger.coloradocollege.edu'},
                 'Smithsonian global sounds for libraries':{'code':'glmu',
                                                            'proxy':'0-glmu.alexanderstreet.com.tiger.coloradocollege.edu'}}

    def __init__(self, marc_file, **kwargs):
        """
        Creates instance of `AlexanderStreetPressMusicBot`


        :param marc_file: MARC file, required
        :param type_of: ASP music database, required
        :param proxy: Proxy preprend, required
        """
        AlexanderStreetPressBase.__init__(self,
                                          marc_file,
                                          **kwargs)
        self.proxy = kwargs['proxy']

    def getResolvedURL(self,
                       marc_record):
        """
        Overrides parent method, ASP music databases resolves to a different URL
        pattern than other ASP databases.

        Parameters:
        - `marc_record`: MARC record, required
        """
        field856 = marc_record.get_fields('856')[0]
        raw_url = field856.get_subfields('u')[0]
        redirect = urllib2.urlopen(raw_url)
        redirect_url = urlparse.urlparse(redirect.geturl())
        self.resolved_baseurl = 'http://%s/View/' % redirect_url.netloc.lower()



    def processRecord(self,
                      marc_record):
        """
        Method process a single MARC record for Alexander Street Press Music
        databases.

        Parameters:
        - `marc_record`: MARC record, required
        """
        if not self.resolved_baseurl:
            self.getResolvedURL(marc_record)
        marc_record = self.validate006(marc_record)
        marc_record = self.validate007(marc_record)
        marc_record = self.remove020(marc_record)
        marc_record = self.validate245(marc_record)
        marc_record = self.validate300(marc_record)
        marc_record = self.remove440(marc_record)
        marc_record = self.remove490(marc_record)
        marc_record = self.validate506(marc_record)
        marc_record = self.validate533(marc_record)
        marc_record = self.validate710(marc_record)
        marc_record = self.validate730(marc_record,
                                       '{0}'.format(self.asp_code))
        marc_record = self.remove830(marc_record)
        marc_record = self.validateURLs(marc_record)
        return marc_record

    def remove020(self,marc_record):
        """
        Removes MARC 020 ISBN field

        Paramaters:
        - `marc_record`: MARC record, required
        """
        return self.__remove_field__(marc_record=marc_record,
                                     tag='020')

    def validate006(self,marc_record):
        """
        Validated 006 with CC standard for sound format
        'm||||||||h||||||||'

        Paramaters:
        - `marc_record`: MARC record, required
        """
        all006fields = marc_record.get_fields('006')
        for field in all006fields:
            marc_record.remove_field(field)
        new006 = Field(tag='006',
                       indicators=[' ',' '],
                       data=r'm        h        ')
        marc_record.add_field(new006)
        return marc_record

    def validate007(self,marc_record):
        """
        Validates 007 fields, if data is sound resource keep, otherwise
        change value to CC standard.

        :param marc_record: MARC record, required
        :rtype marc_record:
        """
        all007s = marc_record.get_fields('007') # Could be Sean Connery, Roger Moore
                                                # Pierce Bronson, or Daniel Craig
                                                # JOKE!
        for field007 in all007s:
            if field007.data.startswith('cr'):
                field007.data = r'cr           u'
        return marc_record

    def validate300(self,marc_record):
        """
        Validates MARC 300 field set subfield a to 'Streaming audio'

        Parameters:
        - `marc_record`: MARC Record, required
        """
        marc_record = self.__remove_field__(marc_record=marc_record,
                                            tag='300')
        new300 = Field(tag='300',
                       indicators=[' ',' '],
                       subfields=['a','Streaming audio'])
        marc_record.add_field(new300)
        return marc_record

    def validateURLs(self,marc_record):
        """
        Validates 856 fields specifically for various types of Alexander
        Street Press music databases.

        Parameters:
        - `marc_record`: MARC record, required
        """
        proxy_location = self.proxy
        all856s = marc_record.get_fields('856')
        for field856 in all856s:
            raw_url = urlparse.urlparse(field856.get_subfields('u')[0])
            record_id = raw_url.query.split(";")[1]
            new_url = "{0}{1}".format(self.resolved_baseurl,record_id)
            field856.delete_subfield('u')
            field856.add_subfield('u',new_url)
        return self.processURLs(marc_record=marc_record,
                                proxy_location=proxy_location,
                                public_note='Listen online')





class GarlandEWMOBot(AlexanderStreetPressBase):
    """
    The `GarlandEWMOBot` process the MARC record
    for the Alexander Street Press Garland Encyclopedia of Music World
    Online electronic resource.
    """

    def __init__(self,**kwargs):
        """
        Creates instance of `GarlandEWMOBot`

        Parameters:
        - `marc_file`: MARC file
        """
        AlexanderStreetPressBaseBot.__init__(self,
                                             marc_file=kwargs.get('marc_file'),
                                             asp_code='aspglnd')
    def getResolvedURL(self,
                       marc_record):
        """
        Overrides parent method, ASP music databases resolves to a different URL
        pattern than other ASP databases.

        Parameters:
        - `marc_record`: MARC record, required
        """
        field856 = marc_record.get_fields('856')[0]
        raw_url = field856.get_subfields('u')[0]
        redirect = urllib2.urlopen(raw_url)
        redirect_url = urlparse.urlparse(redirect.geturl())
        self.resolved_baseurl = 'http://%s/View/' % redirect_url.netloc.lower()


    def processRecord(self,
                      marc_record):
        """
        Method processes a single marc_record for Garland Encyclopedia of
        Music World Online electronic resource.

        Parameters:
        - `marc_record`: MARC record
        """
        if not self.resolved_baseurl:
            self.getResolvedURL(marc_record)
        marc_record = self.validate007(marc_record)
        marc_record = self.validate245(marc_record)
        marc_record = self.remove440(marc_record)
        marc_record = self.remove490(marc_record)
        marc_record = self.validate506(marc_record)
        marc_record = self.validate533(marc_record)
        marc_record = self.validateURLs(marc_record)
        marc_record = self.validate710(marc_record)
        marc_record = self.validate730(marc_record,
                                       "The Garland Encyclopedia of World Music Online")
        marc_record = self.remove830(marc_record)
        return marc_record

    def validateURLs(self,marc_record):
        """
        Validates 856 fields specifically for various types of Alexander
        Street Press music databases.

        Parameters:
        - `marc_record`: MARC record, required
        """
        all856s = marc_record.get_fields('856')
        proxy_location = "0-glnd.alexanderstreet.com.tiger.coloradocollege.edu"
        for field856 in all856s:
            raw_url = urlparse.urlparse(field856.get_subfields('u')[0])
            record_id = raw_url.query.split(";")[1]
            new_url = "%s%s" % (self.resolved_baseurl,record_id)
            field856.delete_subfield('u')
            field856.add_subfield('u',new_url)
        return self.processURLs(marc_record=marc_record,
                                proxy_location=proxy_location)

