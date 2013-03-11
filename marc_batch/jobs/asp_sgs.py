"""
 :mod:`asp_cwm` Alexander Street Press Smithsonian global sounds for libraries Job
"""
__author__ = "Jeremy Nelson"
from asp_base import AlexanderStreetPressMusicJob

class AlexanderStreetPressSmithsonianGlobalSoundsForLibraries(AlexanderStreetPressMusicJob):

    def __init__(self, marc_file, **kwargs):
        """
        Creates instance of `AlexanderStreetPressSmithsonianGlobalSoundsForLibraries`
        """
        kwargs['asp_code'] = 'glmu'
        kwargs['proxy'] = '0-glmu.alexanderstreet.com.tiger.coloradocollege.edu'
        AlexanderStreetPressMusicJob.__init__(self, marc_file, **kwargs)
        
        

    
