__author__ = "Diane Westerfield"
__author__ = "Jeremy Nelson"
from django.views.generic.simple import direct_to_template
from django.contrib.auth import authenticate
from django.http import HttpResponse
from app_settings import APP
from aristotle.views import json_view
from aristotle.settings import INSTITUTION
from dbfinder.redis_helpers import get_databases, get_dbs_alpha, get_dbs_subjects

def alpha(request,letter):
    """
    Returns a list of databases organized by letter
    """
    if request.user.is_authenticated():
        user = request.user
    else:
        user = None
    return direct_to_template(request,
                              'dbfinder/filter.html',
                              {'app':APP,
                               'alpha_dbs':get_dbs_alpha(),
                               'databases':get_databases(letter=letter),
                               'filter':letter,
                               'subject_dbs':get_dbs_subjects(),
                               'institution':INSTITUTION,
                               'user':user})

@json_view
def alpha_json(request,letter):
    output = {"databases":get_databases(letter=letter),
              "name":"{0} Databases starting with {1}".format(INSTITUTION.get('name'),letter)}

    return output
  

def app(request):
    """
    Returns responsive app view for DBFinder App
    """
    if request.user.is_authenticated():
        user = request.user
    else:
        user = None
    return direct_to_template(request,
                              'dbfinder/app.html',
                              {'app':APP,
                               'alpha_dbs':get_dbs_alpha(),
                               'institution':INSTITUTION,
                               'subject_dbs':get_dbs_subjects(),
                               'user':user})

def subject(request,subject_name):
    """
    Returns a subject view of related databases

    :param subject_name: Subject name
    """
    return direct_to_template(request,
                              'dbfinder/filter.html',
                              {'app':APP,
                               'alpha_dbs':get_dbs_alpha(),
                               'databases':get_databases(subject=subject_name),
                               'institution':INSTITUTION,
                               'filter':subject_name,
                               'subject_dbs':get_dbs_subjects(),
                               'user':None})
   
@json_view
def subject_json(request,subject_name):
    return dict(databases=get_databases(subject=subject_name)) 
