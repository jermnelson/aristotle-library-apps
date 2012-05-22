"""

 :mod: views Hours App Views
"""
__author__ = "Jon Driscoll"

from django.views.generic.simple import direct_to_template
from app_settings import APP
import datetime,copy
from django.http import HttpResponse

def default(request):
    """
    default is the standard view for the Hours app
    
    :param request: web request
    """
    return direct_to_template(request,
                               'hours/test-app.html',
                               {'app':APP,
                                'library_status':{'status':True}})

def save(request):
    raw_begins=request.POST["begin"]
    raw_ends=request.POST["end"]
    begins=datetime.datetime.strptime(raw_begins,"%m-%d-%Y")
    ends=datetime.datetime.strptime(raw_ends,"%m-%d-%Y")
    delta = datetime.timedelta(days=1)
    while begins <= ends:
       opentime="%sopen" % begins.strftime("%a").lower()
       closetime="%sclose" % begins.strftime("%a").lower()
       print(opentime,closetime)
       if opentime>closetime:
          midnight=copy.deepcopy(begins)
          midnight.hour=0
          midnight.minute=1
       begins += delta
    return HttpResponse("save %s" % request.POST["monclose"])

