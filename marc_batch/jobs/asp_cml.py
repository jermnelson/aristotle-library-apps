"""
 :mod:`asp_cml` Alexander Street Press Classical Music Library Job
"""
__author__ = "Jeremy Nelson"
from .asp_base import AlexanderStreetPressMusicJob

class AlexanderStreetPressClassicalMusicLibrary(AlexanderStreetPressMusicJob):

    def __init__(self,marc_file,**kwargs):
        """
        Creates instance of `AlexanderStreetPressClassicalMusicLibrary`
        """
        kwargs['asp_code'] = 'clmu'
        kwargs['proxy'] = '0-clmu.alexanderstreet.com.tiger.coloradocollege.edu'
        AlexanderStreetPressMusicJob.__init__(self,marc_file,**kwargs)




