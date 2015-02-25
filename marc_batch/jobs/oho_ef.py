"""
 :mod:`oho_p` Oxford Press Handbooks Online Economics and Finance Job
"""
__author__ = "Jeremy Nelson"
from .op_base import OxfordHandbooksJob

class OxfordHandbooksOnlineEconomicsFinance(OxfordHandbooksJob):
    """
    Class reads Oxford Handbooks Online Economics and Finance MARC21 file and
    modifies per CC's requirements
    """

    def __init__(self,
                 marc_file,
                 **kwargs):
        """
        Initializes an `OxfordHandbooksOnlineEconomicsFinance` class
        """
        OxfordHandbooksJob.__init__(self,
                                    handbook_label = "in economics and finance",
                                    marc_file=marc_file,
                                    **kwargs)


