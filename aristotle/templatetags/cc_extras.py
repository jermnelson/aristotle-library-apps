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
COLLEGE_URL = "{0}{1}".format(LIBRARY_URL.scheme,
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
        output += "{0}\n".format(tag.prettify())
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
        output += "{0}\n".format(tag.prettify())
    cache.set('lib-js', output)
            
        
    
    
def harvest_homepage():
    """
    Function retrieves latest snapshot from live library website,
    uses CSS selectors to save portions of the site to cache.
    """
    try:
        lib_home = urllib2.urlopen(LIBRARY_URL.geturl()).read()
    except urllib2.HTTPError, e:
        logging.error("Unable to open URL {0}".format(LIBRARY_URL.geturl()))
    lib_soup = BeautifulSoup(lib_home)
    for html_id in ["header", "footer", "cc-tabs"]:
        result = lib_soup.select("#{0}".format(html_id))
        if len(result) == 1:
            element = result[0]
            __filter_anchors__(element)
            cache.set('lib-{0}'.format(html_id),
                      element.prettify())
    cache_css(lib_soup)
    cache_js(lib_soup)
    
register = template.Library()


def get_css(cache_key='lib-css'):
    """
    Function returns cached version of css from live site

    :param cache_key: Key to retrieve footer from cache, defaults to 
                      lib-css
    """
    lib_css = cache.get(cache_key)
    if lib_css is not None:
        return mark_safe(lib_css)
    else:
        harvest_homepage()
        return mark_safe(cache.get(cache_key))

def get_footer(cache_key='lib-footer'):
    """
    Function returns cached version of footer element from live site

    :param cache_key: Key to retrieve footer from cache, defaults to 
                      lib-footer
    """
    footer = cache.get(cache_key)
    if footer:
        return mark_safe(footer)
    else:
        harvest_homepage()
        return mark_safe(cache.get(cache_key))

def get_header(cache_key='lib-header'):
    """
    Function returns cached version of header element from live site

    :param cache_key: Key to retrieve header from cache, defaults to 
                      lib-header
    """
    header = cache.get(cache_key)
    if header:
        return mark_safe(header)
    else:
        harvest_homepage()
        return mark_safe(cache.get(cache_key))

def get_js(cache_key='lib-js'):
    """
    Function returns cached version of javascript from live site

    :param cache_key: Key to retrieve footer from cache, defaults to 
                      lib-js

    """
    lib_js = cache.get(cache_key)
    if lib_css is not None:
        return mark_safe(lib_js)
    else:
        harvest_homepage()
        return mark_safe(cache.get(cache_key))

def get_tabs(cache_key='lib-cc-tabs'):
    """Function returns cached version of library-tabs div element from 
    live site

    :param cache_key: Key to retrieve tabs from cache, defaults to 
                      lib-cc-tabs
    """
    tabs = cache.get(cache_key)
    if tabs:
        return mark_safe(tabs)
    else:
        harvest_homepage()
        return mark_safe(cache.get(cache_key))    

register.filter('get_css', get_css)    
register.filter('get_footer', get_footer)    
register.filter('get_header', get_header)
register.filter('get_js', get_css)    
register.filter('get_tabs', get_tabs)
