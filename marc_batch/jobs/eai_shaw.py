"""
 :mod:`eai_evans` Early American Imprints Shaw Job
"""
__author__ = "Jeremy Nelson"
from eai import EarlyAmericanImprintsJob

class EarlyAmericanImprintsShawJob(EarlyAmericanImprintsJob):

    def __init__(self,marc_file,**kwargs):
        """
        Creates instance of `EarlyAmericanImprintsShawJob`
        """
        kwargs['field250_stmt'] = 'Shaw-Shoemaker digital ed.'
        super(EarlyAmericanImprintsShawJob,self).__init__(marc_file,**kwargs)
        

    
