"""Management commands loads title, Person, and Subject authorities into
the Redis Library Services Platform"""
__author__ = "Jeremy Nelson"

import datetime
import os
import pymarc
import sys
from aristotle.settings import REDIS_DATASTORE, PROJECT_HOME
from title_search.whoosh_helpers import index_marc

from django.core.management.base import BaseCommand, CommandError

def __index_titles__(**kwargs):
    redis_ds = kwargs.get('redis_datastore',
                          REDIS_DATASTORE)
    filename = kwargs.get('filename', None)
    if filename is None:
        return
    title_authorities = pymarc.MARCReader(
        open(filename,
             'rb'),
        to_unicode=True)
    start_time = datetime.datetime.utcnow()
    print("Started title indexing at {0}".format(start_time.isoformat()))
    for i, rec in enumerate(title_authorities):
        index_marc(record=rec, redis_datastore=redis_ds)
        if not i%100:
            sys.stderr.write(".")
        if not i%1000:
            print(i)
    end_time = datetime.datetime.utcnow()
    print("End title indexing at {0}, total-time={1}".format(
        end_time.isoformat(),
        end_time-start_time))    
    
    
    

class Command(BaseCommand):
    args = '<marc_filepath authority_type>'
    help = "Indexes Title, Person, and Subject into RLSP and Whoosh indicies"

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError("load_authorities requires marc filepath and "\
                               "authority type")
        filename = args[0]
        authority_type = args[1]
        if authority_type == 'title':
            __index_titles__(filename=filename)
