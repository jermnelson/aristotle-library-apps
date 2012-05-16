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
    

register.filter('app_display',app_display)
