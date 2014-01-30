"""
 :mod:`oho_p` Oxford Press Handbooks Online Philosophy Job
"""
__author__ = "Jeremy Nelson"
from op_base import OxfordHandbooksJob

class OxfordHandbooksOnlinePhilosophy(OxfordHandbooksJob):
    """
    Class reads Oxford Handbooks Online Philosophy MARC21 file and
    modifies per CC's requirements
    """

    def __init__(self,
                 marc_file,
                 **kwargs):
        """
        Initializes an `OxfordHandbooksOnlinePhilosophy` class
        """
        self.handbook_type = "Philosophy"
        OxfordHandbooksJob.__init__(self,
                                    marc_file=marc_file,
                                    **kwargs)


