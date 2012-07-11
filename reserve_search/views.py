"""
 :mod: views Reserve Search App Views
"""
__author__ = "Jon Driscoll & Gautam Webb"

from django.views.generic.simple import direct_to_template
from app_settings import APP
from aristotle.settings import INSTITUTION

def default(request):
    """
    default is the standard view for the article search app
    :param request: web request
    """

    return direct_to_template(request,
                              'reserve_search/app.html',
                              {'app':APP,
                               'institution':INSTITUTION})

def widget(request):
    """
    Returns rendered html snippet of article_search widget
    """

    return direct_to_template(request,
                              'reserve_search/snippets/widget.html',
                              {'app':APP,
                               'standalone':True,
                               'showappicon':True})
