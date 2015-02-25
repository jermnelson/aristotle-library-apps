"""
 :mod:`oho_ps` Oxford Press Handbooks Online Political Science Job
"""
__author__ = "Jeremy Nelson"
from .op_base import OxfordHandbooksJob

class OxfordHandbooksOnlinePoliticalScience(OxfordHandbooksJob):
    """
    Class reads Oxford Handbooks Online Political Science MARC21 file and
    modifies per CC's requirements
    """

    def __init__(self,
                 marc_file,
                 **kwargs):
        """
        Initializes an `OxfordHandbooksOnlinePoliticalScience` class
        """
        OxfordHandbooksJob.__init__(self,
                                    handbook_label='of political science',
                                    marc_file=marc_file,
                                    **kwargs)


