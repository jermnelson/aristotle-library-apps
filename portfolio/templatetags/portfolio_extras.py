"""
 :mod:`call_number_extras` Call Number Application specific tags
"""
__author__ = 'Jeremy Nelson'

import aristotle.settings as settings
import redis
from django.template import Context,Library,loader
from django.utils import simplejson as json
from django.utils.safestring import mark_safe

register = Library()

def app_display(app):
    """
    Generates an App icon for interaction within the Portfolio

    :param app: Application infomation
    :rtype: Generated HTML or NONE
    """
    app_template = loader.get_template('app-icon.html')
    app_dict = {'bk_color':app['background_color'],
                'icon_img':app['icon'],
                'name':app['name'],
                'url':app['url']}
    return mark_safe(app_template.render(Context(app_dict)))


def create_app_td(app):
    """
    Generates a table td for the active app
 
    :param app: App dict
    :rtype: Generated HTML
    """
    app_template = loader.get_template('app-thumbnail.html')
    app_dict = {'app':app}
    
    return mark_safe(app_template.render(Context(app_dict)))

def get_navbar_menu(menu):
    """
    Calls and generates HTML for a Twitter Bootstrap navbar menu

    :param isbn: Numeric ISBN of Book 
    :rtype: Generated HTML or None
    """
    try:
        navbar_template = loader.get_template('navbar-default-menu.html')
        params = {"menu":menu}
        return mark_safe(navbar_template.render(Context(params)))
    except:
        return ''


def test_row(counter):
    """
    Tests if counter%4 is 0

    :param counter: For loop counter 
    :rtype: boolean 
    """
    if counter%4 == 0:
        return True
    return False

register.filter('app_display',app_display)
register.filter('create_app_td',create_app_td)
register.filter('get_navbar_menu',get_navbar_menu)
register.filter('test_row',test_row)

