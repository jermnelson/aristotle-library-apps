"""
 :mod:`asp_bsd2` Alexander Street Press Alexander Street Press Black Drama for
 libraries Job
"""
__author__ = "Jeremy Nelson"
from asp_base import AlexanderStreetPressBase
from pymarc import Field

class AlexanderStreetPressBlackDrama(AlexanderStreetPressBase):
    """
    The `AlexanderStreetPressBlackDrama` reads MARC records from the 2nd Edition
    of the Alexander Street Press Black Drama and supplements
    database.
    """

    def __init__(self, marc_file, **kwargs):
        """
        Creates instance of `BlackDramaBot`

        Parameters:
        - `marc_file`: MARC file, required
        """
        kwargs['asp_code'] = 'asp_bd2'
        AlexanderStreetPressBase.__init__(self, marc_file, **kwargs)

    def processRecord(self,
                      marc_record):
        """
        Method process a single marc_record Black Drama 2nd Edition database

        Parameters:
        - `marc_record`: MARC record, required
        """
        if not self.resolved_baseurl:
            self.getResolvedURL(marc_record)
        marc_record = self.validate006(marc_record)
        marc_record = self.validate007(marc_record)
        marc_record = self.validate245(marc_record)
        marc_record = self.validate250(marc_record)
        marc_record = self.remove440(marc_record)
        marc_record = self.remove490(marc_record)
        marc_record = self.validate506(marc_record)
        marc_record = self.validate533(marc_record)
        marc_record = self.validate710(marc_record)
        marc_record = self.validate730(marc_record,
                                       'Black drama.')
        marc_record = self.remove830(marc_record)
        marc_record = self.validateURLs(marc_record,
                                        '0-solomon.bld2.alexanderstreet.com.tiger.coloradocollege.edu')
        return marc_record

    def validate250(self,marc_record):
        """
        Method adds edition statement to a new 250 field.

        Parameters:
        - `marc_record`: MARC record, required
        """
        new250 = Field(tag='250',
                       indicators=[' ',' '],
                       subfields=['a','2nd ed.'])
        marc_record.add_field(new250)
        return marc_record
