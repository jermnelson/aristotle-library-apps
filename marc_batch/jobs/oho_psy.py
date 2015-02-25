"""
 :mod:`oho_p` Oxford Press Handbooks Online Psychology Job
"""
__author__ = "Jeremy Nelson"
from .op_base import OxfordHandbooksJob

class OxfordHandbooksOnlinePsychology(OxfordHandbooksJob):
    """
    Class reads Oxford Handbooks Online Psychology MARC21 file and
    modifies per CC's requirements
    """

    def __init__(self,
                 marc_file,
                 **kwargs):
        """
        Initializes an `OxfordHandbooksOnlinePsychology` class
        """
        OxfordHandbooksJob.__init__(self,
                                    handbook_label = "of psychology",
                                    marc_file=marc_file,
                                    **kwargs)


