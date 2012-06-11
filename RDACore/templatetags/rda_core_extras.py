__author__ = 'Jeremy Nelson'

from django.template import Context,Library,loader
from django.utils.safestring import mark_safe

register = Library()

def display_facet(facet_info):
    """
    Filter takes information about a facet and generates a DIV from
    a template for inclusion in an facet accordion
    """
    return mark_safe("IN DISPLAY FACET")

register.filter('display_facet',display_facet)
