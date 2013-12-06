"""
 mod:`views` Default Views for Aristotle App
"""
__author__ = 'Jeremy Nelson'

import logging,sys, datetime
from django.http import HttpResponse, Http404

from django.shortcuts import render as direct_to_template # quick hack to get running under django 1.5
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout 
from django.contrib.auth.forms import AuthenticationForm
import django.utils.simplejson as json
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from fixures import json_loader,rst_loader
from aristotle.settings import REDIS_DATASTORE

def background(request):
    """
    Background view for the Aristotle Library Apps project

    :param request: Web request from client
    :rtype: Generated HTML template
    """
    return direct_to_template(request,
                              'background.html',
                              {'app':None,
                               'history':rst_loader.get('project-history'),
                               'institution':json_loader.get('institution'),                               
                               'navbar_menus':json_loader.get('navbar-menus'),
                               'related_resources':rst_loader.get('related-resources'),
                               'user':None})

def default(request):
    """
    Default view for Aristotle Library Apps project

    :param request: Web request from client
    :rtype: Generated HTML template
    """
    app_listing = []
    
    return direct_to_template(request,
                              'index.html',
                              {'app':None,
                               'institution':json_loader.get('institution'),                               
                               'navbar_menus':json_loader.get('navbar-menus'),
                               'portfolio':app_listing,
                               'vision':rst_loader.get('vision-for-aristotle-library-apps'),
                               'user':None})

def app_login(request):
    """
    Attempts to authenticate a user to Aristotle Library Apps 

    :param request: HTTP Request
    """
    if request.method == 'GET':
        return HttpResponse("IN GET App Login")
    username = request.POST['username']
    password = request.POST['password']
    next_page = request.REQUEST.get('next')
    try:
        user = authenticate(last_name=username,
	                    iii_id=password)
    except KeyError:
        user = None
    if user is not None:
        if user.is_active:
            login(request, user)
            if len(next_page) > 0:
                return HttpResponseRedirect(next_page)
            else:
                return HttpResponseRedirect('/')
	else:
            logging.error("User not active")
            raise Http404
    else:
        logging.error("User {0} not found".format(username))
	raise Http404

def app_logout(request):
    """
    Attempts to logout a user from the Aristotle Library Apps 

    :param request: HTTP Request
    """
    if request.REQUEST.has_key('next'):
        next_page = request.REQUEST.get('next')
    else:
        next_page = '/apps'
    logout(request)
    return HttpResponseRedirect(next_page)
   

def feedback(request):
    """
    Feedback view for the Aristotle Library Apps Project

    :param request: Web request from client
    """
    if request.method != 'POST':
        return Http404
    today = datetime.datetime.utcnow()
    feedback_id = REDIS_DATASTORE.incr(
        "global feedback:{0}:{1}".format(today.year,
                                         today.month))
    feedback_key = "feedback:{0}:{1}:{2}".format(today.year, 
		                                 today.month, 
						 feedback_id)
    REDIS_DATASTORE.hset(feedback_key, "created", today.isoformat())
    REDIS_DATASTORE.hset(feedback_key, "comment", request.POST.get('comment'))
    REDIS_DATASTORE.hset(feedback_key, "context", request.POST.get('context'))
    if request.POST.has_key('sender'):
        REDIS_DATASTORE.hset(feedback_key, "sender", request.POST.get('sender'))
    
    return redirect(REDIS_DATASTORE.hget(feedback_key, "context"))
    
    


def starting(request):
    """
    Getting Started view for the Aristotle Library Apps project

    :param request: Web request from client
    :rtype: Generated HTML template
    """
    return direct_to_template(request,
                              'getting-started.html',
                              {'app':None,
                               'steps':[rst_loader.get('installing')],
                               'institution':json_loader.get('institution'),                               
                               'navbar_menus':json_loader.get('navbar-menus'),
                               'user':None})


def website_footer(request):
    """
    Displays a footer replaced by a harvested footer from a website. This
    function is for one example of website interoperbility of the an App
 
    :param request: HTTP Request
    """
    return direct_to_template(request,
                              'snippets/website-footer.html',
                             {})


def website_header(request):
    """
    Displays a footer replaced by a harvested footer from a website. This
    function is for one example of website interoperbility of the an App
 
    :param request: HTTP Request
    """
    return direct_to_template(request,
                              'snippets/website-header.html',
                             {})


    
def json_view(func):
    """
    Returns JSON results from method call, from Django snippets
    `http://djangosnippets.org/snippets/622/`_
    """
    def wrap(request, *a, **kw):
        response = None
        try:
            func_val = func(request, *a, **kw)
            assert isinstance(func_val, dict)
            response = dict(func_val)
            if 'result' not in response:
                response['result'] = 'ok'
        except KeyboardInterrupt:
            raise
        except Exception,e:
            exc_info = sys.exc_info()
            print(exc_info)
            logging.error(exc_info)
            if hasattr(e,'message'):
                msg = e.message
            else:
                msg = ugettext("Internal error: %s" % str(e))
            response = {'result': 'error',
                        'text': msg}
        json_output = json.dumps(response)
        return HttpResponse(json_output,
                            mimetype='application/json')
    return wrap

