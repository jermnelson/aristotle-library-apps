"""

 :mod: views Hours App Views
"""
__author__ = "Jon Driscoll and Jeremy Nelson"

from django.views.generic.simple import direct_to_template
from app_settings import APP
import datetime,copy,urllib
from django.http import HttpResponse,HttpResponseRedirect
from redis_helpers import add_library_hours
from django.shortcuts import redirect

def default(request):
    """
    default is the standard view for the Hours app
    
    :param request: web request
    """
    return direct_to_template(request,
                               'hours/app.html',
                               {'app':APP,
                                'library_status':{'status':True}})

def open(request):
    """
    open is the "we are open" view for the Hours app

    :param request: web request
    """
    return direct_to_template(request,
                               'hours/open.html',
                               {'app':APP})

def closed(request):
    """
    closed is the "we are closed" view for the Hours app

    :param request: web request
    """
    return direct_to_template(request,
                               'hours/closed.html',
                               {'app':APP,})

def manage(request,message):
    """
    manage is the admin view for the Hours app

    :param request: web request
    """
    message=None
    if request.GET.has_key("message"):
        message=request.GET["message"]
    return direct_to_template(request,
                               'hours/app.html',
                               {'app':APP,
                                'library_status':{'status':True},
                                'message':message})

def save(request):
    raw_begins=request.POST["begin"]
    raw_ends=request.POST["end"]
    begins=datetime.datetime.strptime(raw_begins,"%m-%d-%Y")
    starts=copy.deepcopy(begins)
    ends=datetime.datetime.strptime(raw_ends,"%m-%d-%Y")
    delta = datetime.timedelta(days=1)
    while begins <= ends:
       cgiopen="%sopen" % begins.strftime("%a").lower()
       cgiclose="%sclose" % begins.strftime("%a").lower()
       opentime=datetime.datetime.strptime("%s %s" % (begins.strftime("%m-%d-%Y"),request.POST[cgiopen]),
                                           "%m-%d-%Y %I:%M%p")
       closetime=datetime.datetime.strptime("%s %s" % (begins.strftime("%m-%d-%Y"),request.POST[cgiclose]),
                                           "%m-%d-%Y %I:%M%p")
       if opentime>closetime:
          midnight=datetime.datetime(begins.year,begins.month,begins.day,0,0)
          add_library_hours(midnight,closetime)
          lastminute=datetime.datetime(begins.year,begins.month,begins.day,23,59)
          add_library_hours(begins,lastminute)
       else: 
          add_library_hours(opentime,closetime)
       begins += delta
    message="Hours for %s to %s have been set in Redis!" % (starts.strftime("%m-%d-%Y"),ends.strftime("%m-%d-%Y"))
    return HttpResponseRedirect("/apps/hours/manage?message=%s" % urllib.quote(message))
