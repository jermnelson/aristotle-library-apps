"""
 :mod:`oho_r` Oxford Press Handbooks Religion Job
"""
__author__ = "Jeremy Nelson"
from .op_base import OxfordHandbooksJob

class OxfordHandbooksOnlineReligion(OxfordHandbooksJob):
    """
    Class reads Oxford Handbooks Online Religion MARC21 file and
    modifies per CC's requirements
    """

    def __init__(self,
                 marc_file,
                 **kwargs):
        """
        Initializes an `OxfordHandbooksOnlineReligion` class
        """
        OxfordHandbooksJob.__init__(self,
                                    handbook_label=' in religion',
                                    marc_file=marc_file,
                                    **kwargs)


