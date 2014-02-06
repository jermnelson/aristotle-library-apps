"""
 :mod:`cc_extras` Colorado College Specific Tags and functionality
"""
__author__ = "Jeremy Nelson"

import logging
import re
import urllib2
from bs4 import BeautifulSoup
from django.core.cache import cache
from django import template
from django.utils.safestring import mark_safe
from aristotle.settings import INSTITUTION

LIBRARY_URL = urllib2.urlparse.urlparse(INSTITUTION.get('url'))
COLLEGE_URL = "{0}://{1}".format(LIBRARY_URL.scheme,
                                 LIBRARY_URL.netloc)


def __filter_anchors__(element):
    """
    Helper function iterates through all the anchors in the element
    and makes all relative Colorado College home anchors into absolute

    :param element:
    """
    for elem in element.find_all('a'):
        href = elem.attrs.get('href')
        elem.attrs['target'] = '_top'
        if href.startswith("#") or\
           href.startswith("http") or\
           href.startswith("mailto"):
            pass
        else:
            college_webpage = urllib2.urlparse.urljoin(COLLEGE_URL,
                                                       href)
            elem.attrs['href'] = college_webpage


def __filter_imgs__(element):
    """
    Helper function iteraties through all of the img tags in the
    element and makes all img links absolute.

    :param element: Element
    """
    for img in element.find_all('img'):
        src = img.attrs.get('src')
        img.attrs['src'] = urllib2.urlparse.urljoin(COLLEGE_URL,
                                                    src)

def __filter_search_form__(element):
    """
    Helper function takes an element, extracts the form elements and
    makes the form's action an absolute URL

    :param element: Element
    """
    search_form_list = element.select("#search")
    if len(search_form_list) > 0:
        search_form = search_form_list[0]
        action = search_form.attrs.get('action')
        search_form['action'] = urllib2.urlparse.urljoin(COLLEGE_URL,
                                                         action)
        search_form['target'] = '__top__'
        submit_input = search_form.select(".submit")[0]
        submit_input.attrs['src'] = urllib2.urlparse.urljoin(COLLEGE_URL,
                                        submit_input.attrs['src'])

def cache_css(library_soup):
    """
    Retrieves and caches a string of all of the stylesheets from the
    library's homepage.

    :param library_soup: Library Homepage
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

    :param library_soup: Library Homepage
    """
    output = ''
    js_list = library_soup.select('script')
    for tag in js_list:
        src = tag.attrs.get('src')
        if src is not None and\
           not src.startswith('http'):
            tag.attrs['src'] = urllib2.urlparse.urljoin(COLLEGE_URL,
                                                         src)
        output += u"{0}\n".format(tag.prettify())
    cache.set('lib-js', output)

CSS_IMG_RE = re.compile(r"url\((.+)\)")
def cache_tabs(library_soup):
    """
    Function retrieves, modifies, and caches the library tabs

    :param library_soup: Library Homepage
    """
    cache_input = ''
    div_feature_result = library_soup.select('div.feature')
    if len(div_feature_result) == 1:
        div_feature = div_feature_result[0]
        bkgrd_rel_url = CSS_IMG_RE.search(div_feature.attrs.get('style')).groups()[0]
        bkgrd_url = urllib2.urlparse.urljoin(COLLEGE_URL,
                                             bkgrd_rel_url)
        style = '''background-image: url({0}); height: 193px;'''.format(bkgrd_url)
        div_feature.attrs['style'] = style
        cache_input += div_feature.prettify()
    tab_result = library_soup.select('#library-tabs')
    if len(tab_result) == 1:
        library_tabs = tab_result[0]
        __filter_anchors__(library_tabs)
        library_tabs.attrs['style'] = "{0}{1}{2}".format('position: relative;',
                                                         'left: 0px;',
                                                         'top:-175px')
        cache_input += u"\n{0}".format(library_tabs.prettify())
    cache.set('lib-cc-tabs',cache_input)

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
    for html_id in ["header", "footer"]:
        result = lib_soup.select("#{0}".format(html_id))
        if len(result) == 1:
            element = result[0]
            __filter_anchors__(element)
            __filter_imgs__(element)
            __filter_search_form__(element)

            cache.set('lib-{0}'.format(html_id),
                      element.prettify())
    cache_tabs(lib_soup)
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
##    print(u"Tabs are {0} {1}".format(tabs, cache_key))

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
