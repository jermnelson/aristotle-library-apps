"""
#-------------------------------------------------------------------------------
# Name:       oso.py
# Purpose:    Oxford Scholarship Online
#
# Author:      Jeremy Nelson
#
# Created:     2014/10/23
# Copyright:   (c) Jeremy Nelson 2014
# Licence:     GPLv2
#-------------------------------------------------------------------------------
"""
__author__ = 'Jeremy Nelson'

import os
from marc_batch.marc_helpers import MARCModifier
from pymarc import Field
try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse


class OxfordScholarshipOnline(MARCModifier):
    """Class takes any number of different Oxford Scholarship Online and
    generates modified MARC records
    """

    def __init__(self,
                 marc_file,
                 **kwargs):
        """Initializes OxfordScholarshipOnline class

        Args:
            marc_file(file): Original MARC21 file
            collection(str): Oxford Scholarship Online Collection name, optional
            proxy(str): URL proxy, has default
        """
        MARCModifier.__init__(self, marc_file, True)
        self.collection = kwargs.get('collection', None)
        self.proxy = kwargs.get(
            'proxy',
            'http://0-dx.doi.org.tiger.coloradocollege.edu/')



    def processRecord(self, marc_record):
        """Method process MARC21 record

        Args:
            marc_record(pymarc.Record): MARC21 record

        Returns:
            pymarc.Record
        """
        marc_record = self.validate006(marc_record)
        marc_record = self.generate538(marc_record)
        marc_record = self.generate730s(marc_record)
        marc_record = self.replace007(marc_record)
        marc_record = self.validate856(marc_record)
        marc_record.force_utf8 = True
        return marc_record

    def generate538(self, marc_record):
        """Method creates a 538 field following a standard pattern

        Args:
            marc_record(pymarc.Record): MARC21 record

        Returns:
            pymarc.Record
        """
        field856 = marc_record['856']
        original_url = field856['u']
        new538 = Field(tag='538', indicators=[' ',' '])
        new538.add_subfield(
            'a',
            'Available via Internet, {}'.format(original_url))
        marc_record.add_field(new538)
        return marc_record

    def generate730s(self, marc_record):
        """Method creates a 730 field based on collection
        Args:
            marc_record(pymarc.Record): MARC21 record

        Returns:
            pymarc.Record
        """
        new730 = Field(
            tag='730',
            indicators=['0', ' '],
            subfields=['a', 'Oxford scholarship online'])
        marc_record.add_field(new730)
        new730 = Field(
            tag='730',
            indicators=['0', ' '],
            subfields=['a', self.collection])
        marc_record.add_field(new730)
        return marc_record

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
            data=r'cr  n        u'
        new007 = Field(tag='007',data=data)
        marc_record.add_field(new007)
        return marc_record

    def validate006(self, marc_record):
        """Method creates new 006 with the following data m|||||o||d||||||||

        Args:
            marc_record(pymarc.Record): MARC21 record

        Returns:
            pymarc.Record
        """
        marc_record = self.__remove_field__(
            marc_record=marc_record,
            tag='006')
        field006 = Field(tag='006', indicators=None)
        field006.data = r'm     o  d        '
        marc_record.add_field(field006)
        return marc_record

    def validate856(self, marc_record):
        """Method extracts URL from 856 and then creates new 856 with the
        proper proxied URL

        Args:
            marc_record(pymarc.Record): MARC21 record

        Returns:
            pymarc.Record
        """
        field856 = marc_record['856']
        original_url = urlparse.urlparse(field856['u'])
        marc_record = self.__remove_field__(
            marc_record=marc_record,
            tag='856')
        new856 = Field(
            tag='856',
            indicators=['4', '0'],
            subfields=[
                'z', 'View online',
                'u', urlparse.urljoin(self.proxy, original_url.path)])
        marc_record.add_field(new856)
        return marc_record