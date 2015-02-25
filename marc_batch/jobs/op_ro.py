"""
 :mod:`op_ro`  Oxford Reference Online Library Job
"""
__author__ = "Jeremy Nelson"
from .op_base import OxfordHandbooksJob

class OxfordReferenceOnlineJob(OxfordHandbooksJob):
    """
    Class reads Oxford Reference Online MARC file, validates,
    and adds/modifies fields to a new import MARC record for importing
    into TIGER iii ILS.

    """

    def __init__(self, marc_file, **kwargs):
        """
        Initializes `OxfordReferenceOnlineJob`

        :keyword marc_file: Required input MARC file from Oxford Reference
        :keyword proxy_filter: Optional, proxy prefix for 856 field default is REFERENCE_PROXY_FILTER constant.
        :keyword series_title: Optional, default is 'Oxford reference online premium'
        """
        OxfordHandbooksJob.__init__(self,
                                    marc_file=marc_file,
                                    **kwargs)
        if kwargs.has_key('proxy_filter'):
            self.proxy_filter = kwargs.get('proxy_filter')
        else:
            self.proxy_filter = 'http://0-www.oxfordreference.com.tiger.coloradocollege.edu/'
        if kwargs.has_key('series_title'):
            self.series_title = kwargs.get('series_title')
        else:
            self.series_title = 'Oxford reference online premium'

