__author__ = "Diane Westerfield"
__author__ = "Jeremy Nelson"
from django.views.generic.simple import direct_to_template
from django.http import HttpResponse
from app_settings import APP
from aristotle.settings import INSTITUTION
from dbfinder.redis_helpers import get_dbs_alpha, get_dbs_subjects

def app(request):
    """
    Returns responsive app view for DBFinder App
    """
    return direct_to_template(request,
                              'dbfinder/app.html',
                              {'app':APP,
                               'alpha_dbs':get_dbs_alpha(),
                               'institution':INSTITUTION,
                               'subject_dbs':get_dbs_subjects(),
                               'user':None})

 
    
