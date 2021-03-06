"""
 Collection of functions for doing mass updating in BIBFRAME datastore
"""
__author__ = "Jeremy Nelson"
import datetime
import json
import re
import sys
import urllib2
import threading
from aristotle.settings import CREATIVE_WORK_REDIS, INSTANCE_REDIS, ANNOTATION_REDIS
from bibframe.models import CoverArt

ISBN_REGEX = re.compile(r'([0-9\-xX]+)') # from pymarc.record.py
LCCN_REGEX = re.compile(r'([a-w]|[A-W]|[y-z]|[Y-Z]|//]+)')
def UpdateCreativeWorks(function,
                        work_ds=CREATIVE_WORK_REDIS):
    """
    Iterates through all bibframe:Work entities in a datastore
    and applies the function to the entity

    :param function: Function takes the bibframe key as an input and
                     applies processing and updates the key
    :param work_ds: Creative Work Redis datastore
    """
    print("UpdateCreativeWorks")
    UpdateAllEntities('bibframe:Work',
                      function,
                      work_ds)



def UpdateAllEntities(bibframe_key_pattern,
                      function,
                      primary_ds):
    start_time = datetime.datetime.now()
    print("Update {0} started at {1}".format(start_time.isoformat(),
                                             bibframe_key_pattern))
    total_number = int(primary_ds.get('global {0}'.format(bibframe_key_pattern)))
    for counter in range(1, total_number):
        entity_key = '{0}:{1}'.format(bibframe_key_pattern,
                                      counter)
        if primary_ds.exists(entity_key):
            function(entity_key, primary_ds)
    end_time = datetime.datetime.now()
    print("Update ended at {0}, total time = {1} min".format(
        end_time.isoformat(),
        (end_time-start_time).total_seconds() / 60.0))


def CorrectISSNtoISBN(instance_ds):
    for issn in instance_ds.smembers('identifiers:issn:invalid'):
        if instance_ds.hexists('isbn-hash', issn): # ISSN should be ISBN
            
            instance_ds.sadd('identifiers:isbn:invalid', issn)
            instance_ds.srem('identifiers:issn:invalid', issn)
                
def CheckAndAddCoverArt(instance_ds=INSTANCE_REDIS,
                        annotation_ds=ANNOTATION_REDIS,
                        cluster_ds=RLSP_CLUSTER,
                        start=0,
                        end=-1):
    start_time = datetime.datetime.now()
    print("Start at {0}".format(start_time.isoformat()))
    if cluster_ds is not None:
        # Uses lccn-sort-set instead
        for lccn in cluster_ds.zrange('lccn-sort-set',
                                      start,
                                      end):
            lccn = LCCN_REGEX.sub('', lccn).strip()
            open_lib_rec = get_open_library_info(lccn)
            if len(open_lib_rec) > 0:
                info = open_lib_rec.get('LCCN:{0}'.format(lccn),
                                        {})
                if info.has_key('cover'):
                    
                    
                
    else:
        # Do nothing 
        return
    if end is None:
        end = int(instance_ds.get('global bf:Instance'))
    for counter in range(start, end):
        instance_key = 'bf:Instance:{0}'.format(counter)
        already_exists = False
        for annotation_key in instance_ds.smembers(
            "{0}:hasAnnotation".format(instance_key)):
            if annotation_key.startswith('bf:CoverArt'):
                sys.stderr.write(
                    " {0} already has cover art ".format(instance_key))
                already_exists = True
        if already_exists is True:
            continue
        lccn = instance_ds.hget(instance_key, 'lccn')
        if lccn is not None:
            open_lib_rec = get_open_library_info(lccn, instance_key)
            if open_lib_rec.has_key('LCCN:{0}'.format(lccn)):
                info = open_lib_rec.get('LCCN:{0}'.format(lccn))
                if info.has_key('cover'):
                    new_cover = CoverArt(primary_redis=annotation_ds,
                                         annotates=instance_key)
                    setattr(new_cover,
                            'prov:generated',
                            open_lib_rec.get('url'))
                    covers = info.get('cover')
                    if covers.has_key('small'):
                        small_url = covers.get('small')
                        try:
                            if urllib2.urlopen(small_url).getcode() != 404:
                                thumbnail = urllib2.urlopen(small_url).read()
                                setattr(new_cover,
                                        'thumbnail',
                                        thumbnail)
                        except urllib2.HTTPError, e:
                            print("Cannot open small_url of {0}".format(small_url))
                    if covers.has_key('medium'):
                        medium_url = covers.get('medium')
                        try:
                            if urllib2.urlopen(medium_url).getcode() != 404:
                                cover_body = urllib2.urlopen(medium_url).read()
                                setattr(new_cover,
                                        'annotationBody',
                                        cover_body)
                        except urllib2.HTTPError, e:
                            print("Cannot open medium_url of {0}".format(medium_url))
                    if hasattr(new_cover, 'thumbnail') or hasattr(new_cover, 'annotationBody'):
                        new_cover.save()
                        instance_ds.sadd('{0}:hasAnnotation'.format(instance_key),
                                         new_cover.redis_key)
        if not counter%50:
            sys.stderr.write(str(counter))
        else:
            sys.stderr.write(".")
    end_time = datetime.datetime.now()
    print("Update ended at {0}, total time = {1} min".format(
        end_time.isoformat(),
        (end_time-start_time).total_seconds() / 60.0))
                                        
                        
                                        
                
                                
        
def get_open_library_info(lccn=None, instance_key=None):
    def delay():
        return None
    open_lib_url = 'http://openlibrary.org/api/books?bibkeys=LCCN:{0}&format=json&jscmd=data'.format(lccn)
    try:
        open_lib_json = json.load(urllib2.urlopen(open_lib_url))
        timer = threading.Timer(1, delay)
        timer.start()
    except ValueError, e:
        #print("Error opening {0} for LCCN={1}".format(open_lib_url,
        #                                              lccn))
##        error_log = open("open_library_errors.txt", "a")
##        error_log.write("{0}\t{1}\n".format(instance_key,open_lib_url))
##        error_log.close()
        #print(e)
        return {}
    open_lib_json['url'] = open_lib_url
    return open_lib_json
    
def clean_cover_art(instance_ds=INSTANCE_REDIS, annotation_ds=ANNOTATION_REDIS):
    for i in range(1, int(annotation_ds.get('global bibframe:CoverArt'))):
        key = 'bibframe:CoverArt:{0}'.format(i)
        cover_art = annotation_ds.hgetall(key)
        instance_ds.srem("{0}:hasAnnotation".format(cover_art.get('annotates')),
                         key)
        annotation_ds.delete(key)
    annotation_ds.delete('global bibframe:CoverArt')
    
def remove_cover_art(instance_ds):
    for i in range(1, int(instance_ds.get('global bibframe:Instance'))):
        instance_key = "bibframe:Instance:{0}".format(i)
        all_annotations = instance_ds.smembers('{0}:hasAnnotation'.format(instance_key))
        for row in all_annotations:
            if row.startswith('bibframe:CoverArt'):
                instance_ds.srem('{0}:hasAnnotation'.format(instance_key),
                                 row)
        if not i%100:
            sys.stderr.write(str(i))
        else:
            sys.stderr.write(".")
        
