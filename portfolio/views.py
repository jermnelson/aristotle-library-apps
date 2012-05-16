"""
 mod:`views` Views for Portfolio App
"""
__author__ = 'Jeremy Nelson'

import imp,os
from django.views.generic.simple import direct_to_template
import django.utils.simplejson as json
from aristotle.settings import PROJECT_HOME,PROJECT_ROOT,INSTITUTION,INSTALLED_APPS
from app_settings import APP



def get_apps(is_authenticated):
    """
    Helper function returns a list of app information, extracted
    from all apps in installed apps.

    :param is_authenticated: Boolean for user access to productivity apps
    """
    output = []
    print(PROJECT_HOME)
    for row in INSTALLED_APPS:
        if not row.startswith('django') and not row == 'portfolio':
            settings_file = os.path.join(PROJECT_HOME,
                                         row,
                                         "app_settings.py")
            print(settings_file)
            app_settings = imp.load_source(row,settings_file)
            app_info = app_settings.APP
            if app_info.get('is_productivity'):
                if is_authenticated is True:
                    output.append(app_info)
            else:
                output.append(app_info)
    return output
            
        

def default(request):
    """
    Default view for the portfolio app displays both Access and Productivity
    Apps depending on authentication and access rights

    :param request: Web request from client
    :rtype: Generated HTML template
    """
    app_listing = get_apps(request.user.is_authenticated()) 
##    app_listing = [{'background_color':'gold',
##                    'icon':'article_search.png',
##                    'url':'/apps/article_search',
##                    'name':'Article Search',
##                    'is_productivity':False },
##                   {'background_color':'gold',
##                    'icon':'book_search.png',
##                    'url':'/apps/book_search',
##                    'name':'Book Search',
##                    'is_productivity':False},
###                   {'background_color':'gold',
###                    'icon':'budget.png',
###                    'url':'/apps/budget',
###                    'name':'Budget',
###                    'is_productivity':True},
##                   {'background_color':'gold',
##                    'icon':'call_number_search.png',
##                    'url':'/apps/call_number/',
##                    'name':'Call Number Search',
##                    'is_productivity':False}]
###                   {'background_color':'gold',
###                    'icon':'database.png',
###                    'url':'/apps/database',
###                    'name':'Database',
###                    'is_productivity':False},
###                   {'background_color':'gold',
###                    'icon':'Hourglass.png',
###                    'url':'/apps/hours',
###                    'name':'Library Hours',
###                    'is_productivity':False}]
    return direct_to_template(request,
                              'portfolio/app.html',
                              {'app':APP,
                               'institution':INSTITUTION,
                               'portfolio':app_listing,
                               'user':None})
