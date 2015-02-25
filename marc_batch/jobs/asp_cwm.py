"""
 :mod:`asp_cwm` Alexander Street Press Contemporary world music Job
"""
__author__ = "Jeremy Nelson"
from .asp_base import AlexanderStreetPressMusicJob

class AlexanderStreetPressContemporaryWorldMusic(AlexanderStreetPressMusicJob):

    def __init__(self, marc_file, **kwargs):
        """
        Creates instance of `AlexanderStreetPressContemporaryWorldMusic`
        """
        kwargs['asp_code'] = 'womu'
        kwargs['proxy'] = '0-womu.alexanderstreet.com.tiger.coloradocollege.edu'
        AlexanderStreetPressMusicJob.__init__(self, marc_file, **kwargs)




