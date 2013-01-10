"""
 :mod:`eai_evans` Early American Imprints Evans Job
"""
__author__ = "Jeremy Nelson"
from eai import EarlyAmericanImprintsJob

class EarlyAmericanImprintsEvansJob(EarlyAmericanImprintsJob):

    def __init__(self,marc_file,**kwargs):
        """
        Creates instance of `EarlyAmericanImprintsEvansJob`
        """
        kwargs['field250_stmt'] = 'Evans digital ed.'
        super(EarlyAmericanImprintsEvansJob,self).__init__(marc_file,**kwargs)
        

    
