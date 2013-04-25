"""
 :mod:`op_ro`  Oxford Reference Online Library Job
"""
__author__ = "Jeremy Nelson"
from marc_batch.marc_helpers import MARCModifier

class OxfordReferenceOnlineJob(MARCModifier):
    """
    Class reads Oxford Reference Online MARC file, validates,
    and adds/modifies fields to a new import MARC record for importing
    into TIGER iii ILS.
 
    """

    def __init__(self, **kwargs):
        """
        Initializes `OxfordReferenceOnlineJob`

        :keyword marc_file: Required input MARC file from Oxford Reference
        :keyword proxy_filter: Optional, proxy prefix for 856 field default is REFERENCE_PROXY_FILTER constant.
        :keyword series_title: Optional, default is 'Oxford reference online premium'
        """
        marc_file = kwargs.get('marc_file')
        OxfordReferenceOnlineJob.__init__(self, marc_file)
        if kwargs.has_key('proxy_filter'):
            self.proxy_filter = kwargs.get('proxy_filter')
        else:
            self.proxy_filter = 'http://0-www.oxfordreference.com.tiger.coloradocollege.edu/'
        if kwargs.has_key('series_title'):
            self.series_title = kwargs.get('series_title')
        else:
            self.series_title = 'Oxford reference online premium'
