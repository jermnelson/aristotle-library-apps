"""
 :mod:`oho_arch` Oxford Press Handbooks Online Archaeology Job
"""
__author__ = "Jeremy Nelson"
from .op_base import OxfordHandbooksJob

class OxfordHandbooksOnlineArchaeology(OxfordHandbooksJob):
    """
    Class reads Oxford Handbooks Online Archaeology MARC21 file and
    modifies per CC's requirements
    """

    def __init__(self,
                 marc_file,
                 **kwargs):
        """
        Initializes an `OxfordHandbooksOnlineArchaeology` class
        """
        OxfordHandbooksJob.__init__(self,
                                    handbook_label = "in archaeology",
                                    marc_file=marc_file,
                                    **kwargs)


