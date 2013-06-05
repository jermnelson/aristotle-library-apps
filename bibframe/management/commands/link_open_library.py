__author__ = "Jeremy Nelson"

import datetime
import json
import os
import re
import sys
import threading
import urllib
import urllib2
from aristotle.settings import ANNOTATION_REDIS, AUTHORITY_REDIS
from aristotle.settings import CREATIVE_WORK_REDIS, INSTANCE_REDIS
from aristotle.settings import RLSP_CLUSTER
from bibframe.models import CoverArt
from django.core.management.base import BaseCommand, CommandError

ISBN_REGEX = re.compile(r'([0-9\-xX]+)') # from pymarc/record.py
LCCN_REGEX = re.compile(r'([a-w]|[A-W]|[y-z]|[Y-Z]|//]+)')
OPEN_LIBRARY_API = "http://openlibrary.org/api/books?"

def get_open_library_info(number_type='lccn',
                          value=None, 
                          instance_key=None):
    def delay():
        return None
    open_lib_data = {'format':'json', 'jscmd':'data'}
    open_lib_url = OPEN_LIBRARY_API
    if number_type == 'lccn':
        lccn = LCCN_REGEX.sub('', value).strip()
        open_lib_url += "bibkeys=LCCN:{0}".format(lccn)
        
    if number_type == 'isbn':
        isbn = ISBN_REGEX.sub('', value).strip()
        open_lib_url += "bibkeys=ISBN:{0}".format(isbn)
    open_lib_url += '&format=json&jscmd=data'
    try:
        open_lib_json = json.load(urllib2.urlopen(open_lib_url))
        timer = threading.Timer(1, delay)
        timer.start()
    except ValueError, e:
        error_log = open("open_library_errors.txt", "a")
        error_log.write("{0}\t{1}\n".format(instance_key,open_lib_url))
        error_log.close()
        #print("ValueError Instance: {0} {1}".format(instance_key, open_lib_url))
        return {}
    except urllib2.HTTPError, e:
        # Try again in 5 seconds
        print("HTTPError: {0} {1}".format(instance_key, open_lib_url))
        timer = threading.Timer(5, delay)
        timer.start()
        open_lib_json = json.load(urllib2.urlopen(open_lib_url))
    open_lib_json['url'] = open_lib_url
    return open_lib_json


def CheckAndAddCoverArt(covers,
                        ol_url,
                        instance_key,
                        cluster_ds=RLSP_CLUSTER):
    annotationBody, thumbnail = None, None
    def __get_image__(url):
        if not cluster_ds.sismember('bf:CoverArt:urls',
                                    url):
            try:
                if urllib2.urlopen(url).getcode() != 404:
                    image = urllib2.urlopen(url).read()
                    cluster_ds.sadd('bf:CoverArt:urls', url)
                    return image
            except urllib2.HTTPError, e:
                print("Cannot open url of {0}".format(url))
    if covers.has_key('small'):
        small_url = covers.get('small')
        thumbnail = __get_image__(small_url)
    if covers.has_key('medium'):
        medium_url = covers.get('medium')
        annotationBody = __get_image__(medium_url)
    if thumbnail is None and annotationBody is None:
        pass
    else:
        new_cover = CoverArt(primary_redis=cluster_ds,
                             annotates=instance_key)
        setattr(new_cover,
                'prov:generated',
                ol_url)
        if thumbnail is not None:
            setattr(new_cover,
                    'thumbnail',
                    thumbnail)
        if annotationBody is not None:
            setattr(new_cover,
                    'annotationBody',
                    annotationBody)
        new_cover.save()
        cluster_ds.sadd(
            '{0}:hasAnnotation'.format(instance_key),
            new_cover.redis_key)
                        
                    

def OpenLibraryLCCNLinker(**kwargs):
    """Creates LinkedData relationships between Open Library and RLSP

    Keyword arguments:
    cluster_ds -- Cluster Datastore, defaults to RLSP_CLUSTER
    start -- Start in lccn-sort-set, defaults to 0
    end -- End in lccn-sort-set, defaults to -1
    """
    cluster_ds = kwargs.get('cluster_ds', RLSP_CLUSTER)
    start = kwargs.get('start', 0)
    end = kwargs.get('end', -1)
    start_time = datetime.datetime.now()
    counter = 0
    print("Start at {0}".format(start_time.isoformat()))
    for lccn in cluster_ds.zrange('lccn-sort-set',
                                      start,
                                      end):
        instance_key = cluster_ds.hget('lccn-hash', lccn)
        lccn = LCCN_REGEX.sub('', lccn).strip()
        open_lib_rec = get_open_library_info(number_type='lccn',
                                             value=lccn)
        info = open_lib_rec.get('LCCN:{0}'.format(lccn), {})
        # Now processes through individual BIBFRAME entities and
        # overlays Open Library JSON results
        if info.has_key('cover'):
            CheckAndAddCoverArt(cluster_ds=cluster_ds,
                                covers=info.get('cover'),
                                ol_url=open_lib_rec.get('url'),
                                instance_key=instance_key)
        if info.has_key('identifiers'):
            for id_name, id_value in info.get('identifiers').iteritems():
                for row in id_value:
                    cluster_ds.hsetnx(instance_key, id_name, row)
                    cluster_ds.hsetnx('{0}-hash'.format(id_name),
                                      row,
                                      instance_key)
                    cluster_ds.zadd('{0}-sorted-set'.format(id_name),
                                    0,
                                    row)
        if not counter%50:
            sys.stderr.write(str(counter))
        else:
            sys.stderr.write(".")
        counter += 1
    end_time = datetime.datetime.now()
    print("Update ended at {0}, total time = {1} min".format(
        end_time.isoformat(),
        (end_time-start_time).total_seconds() / 60.0))
            
        
        


class Command(BaseCommand):
    args = '<link_open_library id_type start end>'
    help = """Creates LinkedData relationships between Open Library
and RLSP BIBFRAME entities.

"""

    def handle(self, *args, **options):
        id_type, start, end = 'lccn', 0, -1
        if len(args) == 1:
            id_type = args[0]
        elif len(args) == 2:
            id_type, start = args
        elif len(args) == 3:
            id_type, start, end = args
        if id_type == 'lccn':
            OpenLibraryLCCNLinker(
                start=start,
                end=end)
        
