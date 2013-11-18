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



def cover_art_from_title(doc,
                         rlsp_ds=REDIS_DATASTORE):
    """Helper function takes a single document result from an Open Library
    record and Redis datastore, if cover_id exists for the item, attempts to
    download and save thumbnails

    Parameters:
    doc -- raw title string
    rlsp_ds -- Redis datastore, default is REDIS_DATASTORE setting
    """
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
            return
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

def enhance_bibframe_entity(title_entity,
                            redis_ds=REDIS_DATASTORE):
    search_results = open_library_record(
        title_entity.titleValue)
    if search_results is None:
        return
    work_keys = list(redis_ds.smembers("{0}:relatedResource".format(
        title_entity.redis_key)))
    instance_keys = []
    for work_key in work_keys:
        if redis_ds.hexists(work_key, 'hasInstance'):
            instance_keys.append(
                redis_ds.hget(work_key,
                              'hasInstance'))
        else:
            instance_keys.extend(
                list(redis_ds.smembers(
                    "{0}:hasInstance".format(work_key))))
        
    
    if search_results.get('numFound') > 0:
        for doc in search_results.get('docs'):
            isbns = doc.get('isbn')
            cover_art = cover_art_from_title(doc, redis_ds)
            if cover_art is not None:
                for instance_key in instance_keys:
                    redis_ds.sadd("{0}:hasAnnotation".format(
                        instance_key),
                                  cover_art.redis_key)
                    redis_ds.sadd("{0}:hasInstance".format(
                        cover_art.redis_key),
                                  instance_key)
    return instance_keys
                
                
                    
        
                    
def open_library_record(title):
    search_url = urllib2.urlparse.urljoin(
        OPEN_LIBRARY_URL,
        'search.json?{0}'.format(
            urllib.urlencode({'title': title})))
    try:
        return json.load(urllib2.urlopen(search_url))
    except urllib2.HTTPError, e:
        print("Cannot open url of {0}".format(search_url))
        return

                    
                    
                
                
            
        
    
    
