"""
 :mod:`ils` Legacy ILS MARC Batch jobs. This module is the latest iteration
 of the work being done in the Tutt Library cataloging department. We are
 trying to simplify and automate the MARC record manipulation we do to
 MARC records received from our various database vendors.
"""
__author__ = 'Jeremy Nelson'


import pymarc
import copy
from .asp_am import AlexanderStreetPressAmericanSong
from .asp_bd2 import AlexanderStreetPressBlackDrama
from .asp_cml import AlexanderStreetPressClassicalMusicLibrary
from .asp_cwm import AlexanderStreetPressContemporaryWorldMusic
from .asp_jml import AlexanderStreetPressJazzMusicLibrary
from .asp_sgs import AlexanderStreetPressSmithsonianGlobalSoundsForLibraries
from .asp_wsm import AlexanderStreetPressWomenSocialMovements
from .eai_evans import EarlyAmericanImprintsEvansJob
from .eai_shaw import EarlyAmericanImprintsShawJob
from .fod import FilmsOnDemandJob
from .oho_arch import OxfordHandbooksOnlineArchaeology
from .oho_bm import OxfordHandbooksOnlineBusinessAndManagement
from .oho_cah import OxfordHandbooksOnlineClassicalStudies
from .oho_ef import OxfordHandbooksOnlineEconomicsFinance
from .oho_h import OxfordHandbooksOnlineHistory
from .oho_lit import OxfordHandbooksOnlineLiterature
from .oho_m import OxfordHandbooksOnlineMusic
from .oho_p import OxfordHandbooksOnlinePhilosophy
from .oho_ps import OxfordHandbooksOnlinePoliticalScience
from .oho_psy import OxfordHandbooksOnlinePsychology
from .oho_r import OxfordHandbooksOnlineReligion
from .op_ro import OxfordReferenceOnlineJob
from .oso import OxfordScholarshipOnline
from .springer import SpringerEBookJob
from .ybp_ebl import ybp_ebl
from .ybp_ebrary import ybp_ebrary


asp_am = AlexanderStreetPressAmericanSong
asp_bd2 = AlexanderStreetPressBlackDrama
asp_cml = AlexanderStreetPressClassicalMusicLibrary
asp_cwm = AlexanderStreetPressContemporaryWorldMusic
asp_jml = AlexanderStreetPressJazzMusicLibrary
asp_sgs = AlexanderStreetPressSmithsonianGlobalSoundsForLibraries
eai_evans = EarlyAmericanImprintsEvansJob
eai_shaw = EarlyAmericanImprintsShawJob
fod = FilmsOnDemandJob
oho_arch = OxfordHandbooksOnlineArchaeology
oho_bm = OxfordHandbooksOnlineBusinessAndManagement
oho_cah = OxfordHandbooksOnlineClassicalStudies
oho_ef = OxfordHandbooksOnlineEconomicsFinance
oho_h = OxfordHandbooksOnlineHistory
oho_lit = OxfordHandbooksOnlineLiterature
oho_m = OxfordHandbooksOnlineMusic
oho_p = OxfordHandbooksOnlinePhilosophy
oho_ps = OxfordHandbooksOnlinePoliticalScience
oho_psy = OxfordHandbooksOnlinePsychology
oho_r = OxfordHandbooksOnlineReligion
op_ro = OxfordReferenceOnlineJob
oso = OxfordScholarshipOnline
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



