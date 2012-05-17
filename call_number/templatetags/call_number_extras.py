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

def google_book_display(isbn):
    """
    Calls and generates HTML for Call Number Widget
    browser.    

    :param isbn: Numeric ISBN of Book 
    :rtype: Generated HTML or None
    """
    try:
        book_json = json.load(urllib2.urlopen(settings.GBS_BASE_URL % isbn))
        gbs_template = loader.get_template('google-book.html')
        for item in book_json["items"]:
            if item['volumeInfo'].has_key('imageLinks'):
                params = {'item':item,
                          'gbs_preview_url':settings.GBS_PREVIEW_URL}
                return mark_safe(gbs_template.render(Context(params)))
    except:
        return ''

register.filter('google_book_display',google_book_display)
