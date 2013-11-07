__author__ = "Jeremy Nelson"

import json
import urllib
import urllib2

from aristotle.settings import REDIS_DATASTORE
from bibframe.models import CoverArt


OPEN_LIBRARY_URL = 'http://openlibrary.org'
OPEN_LIBRARY_COVER_URL = 'http://covers.openlibrary.org/b/id/'

def __get_image__(url):
    if not redis_datastore.sismember('bf:CoverArt:urls',
                                    url):
            try:
                if urllib2.urlopen(url).getcode() != 404:
                    image = urllib2.urlopen(url).read()
                    redis_datastore.sadd('bf:CoverArt:urls', url)
                    return image
            except urllib2.HTTPError, e:
                print("Cannot open url of {0}".format(url))

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
    search_url = urllib2.urlparse.urljoin(
        OPEN_LIBRARY_URL,
        'search.json?{0}'.format(
            urllib.urlencode({'title': title})))
    try:
        search_results = json.load(urllib2.urlopen(search_url))
    except urllib2.HTTPError, e:
        print("Cannot open url of {0}".format(search_url))
        return
    thumbnail, annotationBody = None, None
    if search_results.get('numFound') > 0:
        # Iterates through all found docs, creates and returns CoverArt
        # for first found image
        for doc in search_results.get('docs'):
            if 'cover_i' in doc:
                cover_id = doc.get('cover_i')
                thumbnail_cover_url = urllib2.urlparse.urljoin(
                    OPEN_LIBRARY_COVER_URL,
                    '{0}-S.jpg'.format(
                        cover_id))
                body_cover_url = urllib2.urlparse.urljoin(
                    OPEN_LIBRARY_COVER_URL,
                    '{0}-M.jpg'.format(cover_id))
                if urllib2.urlopen(thumbnail_cover_url).getcode() != 404:
                    thumbnail = urllib2.urlopen(
                        thumbnail_cover_url).read()
                if  urllib2.urlopen(body_cover_url).getcode() != 404:
                    annotationBody = urllib2.urlopen(
                        body_cover_url).read()
                if not thumbnail and not annotationBody:
                    continue
                cover_art = CoverArt(redis_datastore=rlsp_ds)
                if thumbnail:
                    setattr(cover_art,
                            'thumbnail',
                            thumbnail)
                if annotationBody:
                    setattr(cover_art,
                            'annotationBody',
                            annotationBody)
                cover_art.save()
                return cover_art
            
                    
                    
                    
                    
                
                
            
        
    
    
