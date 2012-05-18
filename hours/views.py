"""

 :mod: views Hours App Views
"""
__author__ = "Jon Driscoll"

from django.views.generic.simple import direct_to_template
from app_settings import APP

def default(request):
    """
    default is the standard view for the Hours app
    
    :param request: web request
    """
    return direct_to_template(request,
                               'hours/test-app.html',
                               {'app':APP,
                                'library_status':{'status':True}})
