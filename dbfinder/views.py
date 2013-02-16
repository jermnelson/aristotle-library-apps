__author__ = "Diane Westerfield"
__author__ = "Jeremy Nelson"
from django.views.generic.simple import direct_to_template
from django.http import HttpResponse
from app_settings import APP
from aristotle.settings import INSTITUTION
from dbfinder.redis_helpers import get_databases, get_dbs_alpha, get_dbs_subjects

def alpha(request,letter):
    """
    Returns a list of databases organized by letter
    """
    return direct_to_template(request,
                              'dbfinder/filter.html',
                              {'app':APP,
                               'databases':get_databases(letter=letter),
                               'filter':letter,
                               'institution':INSTITUTION,
                               'user':None})
  

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

def subject(request,subject_name):
    """
    Returns a subject view of related databases

    :param subject_name: Subject name
    """
    return direct_to_template(request,
                              'dbfinder/filter.html',
                              {'app':APP,
                               'databases':get_databases(subject=subject_name),
                               'institution':INSTITUTION,
                               'filter':subject_name,
                               'user':None})
    
