"""
 :mod:`aristotle_extras` General tags for Aristotle Library Apps
"""
__author__ = 'Jeremy Nelson'
import aristotle.settings as settings
import redis
from django.template import Context,Library,loader
from django.utils import simplejson as json
from django.contrib.auth.forms import AuthenticationForm
from django.utils.safestring import mark_safe

register = Library()

def get_login_dlg(csrf_token):
    """
    Returns rendered Login Modal for Apps
    """
    print("CSRF_TOKEN is {0}".format(csrf_token))
    try:
        login_template = loader.get_template('registration/login.html')
        params = {"form": AuthenticationForm(),
                  "passthrough_token":csrf_token}
        return mark_safe(login_template.render(Context(params)))
    except:
        return

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
        return 

register.filter('get_login_dlg', get_login_dlg)
register.filter('get_navbar_menu',get_navbar_menu)
