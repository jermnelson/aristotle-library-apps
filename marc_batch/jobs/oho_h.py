"""
 :mod:`oho_p` Oxford Press Handbooks Online History Job
"""
__author__ = "Jeremy Nelson"
from .op_base import OxfordHandbooksJob

class OxfordHandbooksOnlineHistory(OxfordHandbooksJob):
    """
    Class reads Oxford Handbooks Online History MARC21 file and
    modifies per CC's requirements
    """

    def __init__(self,
                 marc_file,
                 **kwargs):
        """
        Initializes an `OxfordHandbooksOnlineHistory` class
        """
        OxfordHandbooksJob.__init__(self,
                                    handbook_label = "in history",
                                    marc_file=marc_file,
                                    **kwargs)


