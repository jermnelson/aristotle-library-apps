"""
 :mod:`ils` Legacy ILS MARC Batch jobs. This module is the latest iteration
 of the work being done in the Tutt Library cataloging department. We are
 trying to simplify and automate the MARC record manipulation we do to 
 MARC records received from our various database vendors.
"""
__author__ = 'Jeremy Nelson'


import pymarc,copy
from asp_cml import AlexanderStreetPressClassicalMusicLibrary
from asp_jml import AlexanderStreetPressJazzMusicLibrary
from eai_evans import EarlyAmericanImprintsEvansJob
from eai_shaw import EarlyAmericanImprintsShawJob
from springer import SpringerEBookJob
from ybp_ebl import ybp_ebl
from ybp_ebrary import ybp_ebrary


asp_cml = AlexanderStreetPressClassicalMusicLibrary
asp_jml = AlexanderStreetPressJazzMusicLibrary
eai_evans = EarlyAmericanImprintsEvansJob
eai_shaw = EarlyAmericanImprintsShawJob
springer = SpringerEBookJob
ybp_ebl = ybp_ebl
ybp_ebrary = ybp_ebrary


class job(object):
    """
     :class:`ils.job` takes a MARC record and optional job specific
     features to manipulate the MARC record to confirm the scenarios
     set in the features files.
    """

    def __init__(self,
                 marc_record,
                 features=[]):
        """
        Initializes :class:`ils.job` and creates Features

        :param marc_record: MARC record
        :param features: List of features file names, optional
        """
        self.original_record = marc_record
        self.marc_record = marc_record
        

    def run(self):
        """
        Iterates through list of features, applying scenarios and
        then saving the results to the modified_marc record.
        """
        try:
            pass
##            for feature in self.features:
##                feature.run()
        except:
            pass
            
                 

