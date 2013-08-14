"""Module provides web services supporting the management of materials into the
Redis Library Services Platform

BIBFRAME entities i
"""
__author__ = "Jeremy Nelson"

import datetime
import json
import time
import urllib
import urllib2

from aristotle.settings import GOOGLE_API_KEY, REDIS_DATASTORE
from bibframe.models import CoverArt, Description


def enhance_with_google_book(instance_key):
    """Function takes an id name, value, and enhances BIBFRAME entities.
     
    Keywords:
    instance -- BIBFRAME Instance
    """
    params = {'key': GOOGLE_API_KEY}
    for id_name in ['isbn', 'issn']:
        id_value = REDIS_DATASTORE.hget(instance_key, id_name)
        if id_value is not None:
            params['q'] = '{0}:{1}'.format(id_name,
                                           id_value)
            break
    if params.has_key('q'):
        goog_url = 'https://www.googleapis.com/books/v1/volumes?{0}'.format(
            urllib.urlencode(params))
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        opener.addheaders = [('User-Agent',
                              'Mozilla/5.0 (Windows; U; Windows NT5.1; en-US; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')]
        book_json = json.load(urllib2.urlopen(goog_url))
        if book_json.has_key('items'):
            for item in book_json['items']:
                dateOfAssertion=datetime.datetime.utcnow()
                # Create a Google Books Description of the Instance
                google_desc = Description(annotates=instance_key,
                                          annotationSource=item["volumeInfo"]["infoLink"],
                                          dateOfAssertion=dateOfAssertion.isoformat(),
                                          label="Google Description of {0}".format(
                                              item['volumeInfo'].get('title')),
                                          redis_datastore=REDIS_DATASTORE)
                setattr(google_desc,
                        'prov:generated',
                        goog_url)
                google_desc.save()
                REDIS_DATASTORE.sadd(
                    '{0}:hasAnnotation'.format(instance_key),
                    google_desc.redis_key)
                if item['volumeInfo'].has_key('imageLinks'):
                    new_cover = CoverArt(annotates=instance_key,
                                         dateOfAssertion=dateOfAssertion.isoformat(),
                                         redis_datastore=REDIS_DATASTORE)
                    setattr(new_cover,
                            'prov:generated',
                            goog_url)
                    if item['volumeInfo']['imageLinks'].has_key('smallThumbnail'):
                        img_url = item['volumeInfo']['imageLinks']['smallThumbnail']
                        request = urllib2.Request(img_url)
                        data = opener.open(request).read()
                        setattr(new_cover,
                                'thumbnail',
                                data)
                    if item['volumeInfo']['imageLinks'].has_key('thumbnail'):
                        img_url = item['volumeInfo']['imageLinks']['thumbnail']
                        request = urllib2.Request(img_url)
                        data = opener.open(request).read()
                        setattr(new_cover,
                                'annotationBody',
                                data)
                    new_cover.save()
                    REDIS_DATASTORE.sadd(
                        '{0}:hasAnnotation'.format(instance_key),
                        new_cover.redis_key)
                    
                    
                        
                    
                    
                    
                
                    
                                         
            

    
