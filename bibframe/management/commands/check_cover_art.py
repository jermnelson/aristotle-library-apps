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
    if number_type == 'lccn':
        lccn = LCCN_REGEX.sub('', value).strip()
        open_lib_data['bibkeys'] = "LCCN:{0}"
    if number_type == 'isbn':
        isbn = ISBN_REGEX.sub('', value).strip()
        open_lib_data['bibkeys'] = 'ISBN:{0}'
    open_lib_url = OPEN_LIBRARY_API + urllib.urlencode(open_lib_data)
    try:
        open_lib_json = json.load(urllib2.urlopen(open_lib_url))
        timer = threading.Timer(1, delay)
        timer.start()
    except ValueError, e:
        error_log = open("open_library_errors.txt", "a")
        error_log.write("{0}\t{1}\n".format(instance_key,open_lib_url))
        error_log.close()
        print("ValueError Instance: {0} {1}".format(instance_key, open_lib_url))
        return {}
    except urllib2.HTTPError, e:
        # Try again in 5 seconds
        print("HTTPError: {0} {1}".format(instance_key, open_lib_url))
        timer = threading.Timer(5, delay)
        timer.start()
        open_lib_json = json.load(urllib2.urlopen(open_lib_url))
    open_lib_json['url'] = open_lib_url
    return open_lib_json

def CheckAndAddCoverArt(instance_ds=INSTANCE_REDIS,
                        annotation_ds=ANNOTATION_REDIS,
                        type_cover_art='lccn',
                        start=1,
                        end=None):
    start_time = datetime.datetime.now()
    print("Start at {0}".format(start_time.isoformat()))
    if end is None:
        end = int(instance_ds.get('global bibframe:Instance'))
    for counter in range(start, end):
        instance_key = 'bibframe:Instance:{0}'.format(counter)
        already_exists = False
        for annotation_key in instance_ds.smembers("{0}:hasAnnotation".format(instance_key)):
            if annotation_key.startswith('bibframe:CoverArt'):
                sys.stderr.write(" {0} already has cover art ".format(instance_key))
                already_exists = True
        if already_exists is True:
            continue
        id_value = instance_ds.hget(instance_key, type_cover_art)
        if id_value is not None:
            info = {}
            open_lib_rec = get_open_library_info(id_value, instance_key)
            if open_lib_rec.has_key('LCCN:{0}'.format(id_value)):
                info = open_lib_rec.get('LCCN:{0}'.format(id_value))
            elif open_lib_rec.has_key('ISBN:{0}'.format(id_value)):
                info = open_lib_rec.get('ISBN:{0}'.format(id_value))
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


class Command(BaseCommand):
    args = '<check_cover_art id_type instance_start>'
    help = "Checks if cover_art is available for each Instance in the BIBFRAME Datastore"

    def handle(self, *args, **options):
        id_type, instance_start = 'lccn', 0
        if len(args) == 1:
            id_type = args[0]
        elif len(args) == 2:
            id_type, instance_start = args
        CheckAndAddCoverArt(type_cover_art=id_type,
                            start=instance_start)
        