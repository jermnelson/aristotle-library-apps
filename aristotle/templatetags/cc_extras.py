"""
 :mod:`cc_extras` Colorado College Specific Tags and functionality 
"""
__author__ = "Jeremy Nelson"

import urllib2
from bs4 import BeautifulSoup
from django.core.cache import cache
from django import template
from django.utils.safestring import mark_safe
from aristotle.settings import INSTITUTION

LIBRARY_URL = urllib2.urlparse.urlparse(INSTITUTION.get('url'))
COLLEGE_URL = "{0}{1}".format(LIBRARY_URL.schema,
                              LIBRARY_URL.netloc)


def __filter_anchors__(element):
    """
    Helper function iterates through all the anchors in the element
    and makes all relative Colorado College home anchors into absolute

    :param element:
    """
    for elem in element.find_all('a'):
        href = elem.attrs.get('href')
        if href.startswith("#") or\
           href.startswith("http") or\
           href.startswith("mailto"):
            pass
        else:
            elem.attrs['href'] = urllib2.urlparse.urljoin(COLLEGE_URL,
                                                          href)

def cache_css(library_soup):
    """
    Retrieves and caches a string of all of the stylesheets from the
    library's homepage.

    :param library_soup:
    """
    output = ''
    css_list = library_soup.select('link[rel="stylesheet"]')
    for tag in css_list:
        href = tag.attrs.get('href')
        if not href.startswith('http'):
            tag.attrs['href'] = urllib2.urlparse.urljoin(COLLEGE_URL,
                                                            href)
        output += tag.prettify()
    cache.set('lib-css', output)

def cache_js(library_soup):
    """
    Retrieves and caches a string of all of the javascript from the
    library's homepage.

    :param library_soup:
    """
    output = ''
    js_list = library_soup.select('script')
    for tag in js_list:
        src = tag.attrs.get('src')
        if src is not None and\
           not src.startswith('http'):
            tag.attrs['href'] = urllib2.urlparse.urljoin(COLLEGE_URL,
                                                         src)
        output += tag.prettify()
    cache.set('lib-js', output)
            
        
    
    
def harvest_homepage():
    """
    Function retrieves latest snapshot from live library website,
    uses CSS selectors to save portions of the site to cache.
    """
    try:
        lib_home = urllib2.urlopen().read(LIBRARY_URL.geturl())
    except urllib2.HTTPError, e:
        logging.error("Unable to open URL {0}".format(LIBRARY_URL.geturl()))
    lib_soup = BeautifulSoup(cc_home)
    for html_id in ["header", "footer", "cc-tabs"]:
        result = lib_soup.select("#{0}".format(html_id))
        if len(result) == 1:
            element = result[0]
            __filter_anchors__(element)
            cache.set('lib-{0}'.format(html_id),
                      header.prettify())
    cache_css()
    cache_js()
    
register = template.Library()


def get_footer(cache_key='cc-footer'):
    """Function returns cached version of footer element from live CC site

    :param cache_key: Key to retrieve footer from cache, defaults to 
                      cc-footer
    """
    footer = cache.get(cache_key)
    if footer:
        return mark_safe(footer)
    else:
        harvest_latest()
        return mark_safe(cache.get(cache_key))

def get_header(cache_key='cc-header'):
    """Function returns cached version of header element from live CC site

    :param cache_key: Key to retrieve header from cache, defaults to 
                      cc-header
    """
    header = cache.get(cache_key)
    if header:
        return mark_safe(header)
    else:
        harvest_latest()
        return mark_safe(cache.get(cache_key))

def get_tabs(cache_key='cc-tabs'):
    """Function returns cached version of library-tabs div element from 
    live CC site

    :param cache_key: Key to retrieve tabs from cache, defaults to 
                      cc-tabs
    """
    tabs = cache.get(cache_key)
    if tabs:
        return mark_safe(tabs)
    else:
        harvest_latest()
        return mark_safe(cache.get(cache_key))    
        
register.filter('get_footer', get_footer)    
register.filter('get_header', get_header)
register.filter('get_tabs', get_tabs)
