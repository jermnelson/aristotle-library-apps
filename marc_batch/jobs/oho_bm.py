"""
 :mod:`oho_bm` Oxford Press Handbooks Online Business & Management
"""
__author__ = "Jeremy Nelson"
from op_base import OxfordHandbooksJob

class OxfordHandbooksOnlineBusinessAndManagement(OxfordHandbooksJob):
    """
    Class reads Oxford Handbooks Online Business and Management MARC21 file and
    modifies per CC's requirements
    """

    def __init__(self,
                 **kwargs):
        """
        Initializes an `OxfordHandbooksOnlineBusinessAndManagement` class
        """
        OxfordHandbooksJob.__init__(self,
                                    marc_file,
                                    **kwargs)
        
        
