"""
 :mod: views Book Search App Views
"""
__author__ = "Gautam Webb"

from django.views.generic.simple import direct_to_template
from app_settings import APP
from article_search.app_settings import APP as article_app
from aristotle.settings import INSTITUTION

def default(request):
    """
    default is the standard view for the book search app
    :param request: web request
    """

    return direct_to_template(request,
                              'book_search/app.html',
                              {'app':APP,
                               'institution':INSTITUTION})
def widget(request):
    """
    Returns rendered html snippet of book_search widget
    """
    return direct_to_template(request,
                              'book_search/snippets/widget.html',
                              {'app':APP,
                               'standalone':True,
                               'showappicon':True})

def dotCMS(request):
    """
    Returns rendered book and article search in the same widget
    view, kludge to work in dotCMS
    """
    return direct_to_template(request,
                              'snippets/dotCMS-search.html',
                              {'book_app':APP,
                               'article_app':article_app,
                               'showappicon':True,
                               'dotCMS':True})

def dotCMSspeccoll(request):
    """
    Returns rendered html snippet of book_search widget
    """
    return direct_to_template(request,
                              'book_search/snippets/dotCMS-speccoll.html',
                              {'app':APP,
                               'standalone':True,
                               'showappicon':False})

def dotCMSnarrow(request):
    """
    Returns rendered book and article search in the same widget
    view, kludge to work in dotCMS
    """
    return direct_to_template(request,
                              'snippets/dotCMS-narrow.html',
                              {'book_app':APP,
                               'article_app':article_app,
                               'showappicon':False,
                               'usedropup':True})

