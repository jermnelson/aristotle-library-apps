__author__ = "Jeremy Nelson"

import json
import urllib
import urllib2

from aristotle.settings import REDIS_DATASTORE
from bibframe.models import CoverArt


OPEN_LIBRARY_URL = 'http://openlibrary.org'
OPEN_LIBRARY_COVER_URL = 'http://covers.openlibrary.org/b/id/'

def cover_art_from_title(title,
                         rlsp_ds=REDIS_DATASTORE):
    """Helper function takes a title string and Redis datastore,
    attempts to download json for the title from openlibrary.org
    and if cover_id exists for the first item, attempts to
    download and save thumbnails

    Parameters:
    title -- raw title string
    rlsp_ds -- Redis datastore, default is REDIS_DATASTORE setting
    """
    annotationBody, thumbnail = None, None
    search_url = urllib2.urljoin(OPEN_LIBRARY_URL,
                                 'search.json?{0}'.format(
                                     urllib.urlencode(
                                         {'title': title})))
    search_results = json.load(urllib2.urlopen(search_url))
    if search_results.get('numFound') > 0:
        # Iterates through all found docs, creates and returns CoverArt
        # for first found image
        for doc in search_results.get('docs'):
            if 'cover_i' in doc:
                cover_id = doc.get('cover_i')
                thumbnail_cover_url = urllib2.urljoin(OPEN_LIBRARY_URL,
                                                      '{0}-S.jpg'.format(
                                                          cover_id))
                body_cover_url = urllib2.urljoin(OPEN_LIBRARY_URL,
                                                 '{0}-M.jpg'.format(cover_id))
                
                
            
        
    
    
