"""
 :mod:`dbfinder_extras` DBFinder App specific tags and filters
"""
__author__ = "Jeremy Nelson"

import aristotle.settings as settings
from django.template import Context, Library, loader
from django.utils.safestring import mark_safe

register = Library()


def get_discovery_link(entity_key):
    """
    Creates a link to the a BIBFRAME entity in the Discovery App
    """
    if len(entity_key) > 0:
        entity_list = entity_key.split(":")
        output = '''<a href="/apps/discovery/{0}/{1}/">{2}</a>'''.format(entity_list[-2],
                                                                         entity_list[-1],
                                                                         entity_key)
        return mark_safe(output)


register.filter('get_discovery_link',get_discovery_link)
