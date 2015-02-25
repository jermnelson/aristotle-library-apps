"""
 :mod:`oho_p` Oxford Press Handbooks Online Music Job
"""
__author__ = "Jeremy Nelson"
from .op_base import OxfordHandbooksJob

class OxfordHandbooksOnlineMusic(OxfordHandbooksJob):
    """
    Class reads Oxford Handbooks Online Music MARC21 file and
    modifies per CC's requirements
    """

    def __init__(self,
                 marc_file,
                 **kwargs):
        """
        Initializes an `OxfordHandbooksOnlineMusic` class
        """
        OxfordHandbooksJob.__init__(self,
                                    handbook_label = "in music",
                                    marc_file=marc_file,
                                    to_unicode=True,
                                    **kwargs)


