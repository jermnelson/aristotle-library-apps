"""
 :mod:`asp_wsm` Alexander Street Press Women Social Movements Job
"""
__author__ = "Jeremy Nelson"
from asp_base import AlexanderStreetPressBase
            
class AlexanderStreetPressWomenSocialMovements(AlexanderStreetPressBase):
    """
    The `AlexanderStreetPressWomenSocialMovements` reads MARC records from
    Alexander Street Press Women and Social Movements database.
    """

    def __init__(self,**kwargs):
        """
        Creates instance of `WomenSocialMovementsBot`

        Parameters:
        - `marc_file`: MARC file
        """
        kwargs['asp_code'] = 'aspw'
        AlexanderStreetPressBase.__init__(self, marc_file, **kwargs)
        
    def processRecord(self,
                      marc_record):
        """
        Method processes a single marc_record for Women and Social Movements database.

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
        marc_record = self.validateURLs(marc_record,
                                        "0-asp6new.alexanderstreet.com.tiger.coloradocollege.edu")
        marc_record = self.validate710(marc_record)
        marc_record = self.validate730(marc_record,
                                       "Women and social movements in the United States 1600-2000: Scholar's edition.")
        marc_record = self.remove830(marc_record)
        return marc_record


    def validate001(self,marc_record):
        """
        Method follows Prospector best practices for 001 MARC
        field.

        Parameters:
        - `marc_record`: MARC record, required
        """
        field001 = marc_record.get_fields('001')[0]
        marc_record.remove_field(field001)
        return marc_record
