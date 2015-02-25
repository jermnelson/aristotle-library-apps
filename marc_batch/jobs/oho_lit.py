"""
 :mod:`oho_p` Oxford Press Handbooks Online Literature Job
"""
__author__ = "Jeremy Nelson"
from .op_base import OxfordHandbooksJob

class OxfordHandbooksOnlineLiterature(OxfordHandbooksJob):
    """
    Class reads Oxford Handbooks Online Literature MARC21 file and
    modifies per CC's requirements
    """

    def __init__(self,
                 marc_file,
                 **kwargs):
        """
        Initializes an `OxfordHandbooksOnlineLiterature` class
        """
        OxfordHandbooksJob.__init__(self,
                                    handbook_label = "of literature",
                                    marc_file=marc_file,
                                    **kwargs)


