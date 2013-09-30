"""Management commands loads title, Person, and Subject authorities into
the Redis Library Services Platform"""
__author__ = "Jeremy Nelson"

import datetime
import os
import sys
from aristotle.settings import REDIS_DATASTORE, PROJECT_HOME
from django.core.management.base import BaseCommand, CommandError

def __index_titles__(**kwargs):
    redis_ds = kwargs.get('redis_datastore',
                          REDIS_DATASTORE)
    filename = kwargs.get('filename', None)
    if filename is None:
        return
    title_authorities = pymarc.MARCReader(
        open(filepath,
             'rb'),
        to_unicode=True)
    start_time = datetime.datetime.utcnow()
    print("Started title indexing at {0}".format(start_time.isoformat()))
    for i, rec in enumerate(title_authorities):
        index_marc(record=rec,
                    redis_datastore=rlsp_ds)
        if not i%100:
            sys.stderr.write(".")
        if not i%1000:
            print(i)
    end_time = datetime.datetime.utcnow()
    print("End title indexing at {0}, total-time={1}".format(
        end_time.isoformat(),
        end_time-start_time))    
    
    
    

class Command(BaseCommand):
    args = ''
    help = "Indexes Title, Person, and Subject into RLSP and Whoosh indicies"

    def handle(self, *args, **options):
        __index_titles__(**options)
