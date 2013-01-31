"""
 :mod:`ingesters` Module ingests MARC21 and MODS records into a MARCR-Redis datastore
 controlled by the MARCR app.
"""
__author__ = "Jeremy Nelson"

import datetime, re, pymarc, os, sys,logging, redis, time
from bibframe.models import Annotation, Organization, Work, Instance, Person
from call_number.redis_helpers import generate_call_number_app
from person_authority.redis_helpers import get_or_generate_person
from aristotle.settings import PROJECT_HOME
from title_search.redis_helpers import generate_title_app,search_title
import marc21_facets
from MARC21 import MARC21toBIBFRAME
from lxml import etree
from rdflib import RDF,RDFS,Namespace
import json

STD_SOURCE_CODES = json.load(open(os.path.join(PROJECT_HOME,
                                               'bibframe',
                                               'fixures',
                                               'standard-id-src-codes.json'),
                                  'rb'))

BF = Namespace('http://bibframe.org/model-abstract/')

def ingest_marcfile(**kwargs):
    marc_filename = kwargs.get("marc_filename")
    annotation_ds = kwargs.get('annotation_redis')
    authority_ds = kwargs.get('authority_redis')
    creative_work_ds = kwargs.get("creative_work_redis")
    instance_ds =kwargs.get("instance_redis")
    if marc_filename is not None:
        marc_file = open(marc_filename,'rb')
        count = 0
        marc_reader = pymarc.MARCReader(marc_file,
                                        utf8_handling='ignore')
        start_time = datetime.datetime.now()
        sys.stderr.write("Starting at {0}\n".format(start_time.isoformat()))
        for record in marc_reader:
            ingester = MARC21toBIBFRAME(annotation_ds=annotation_ds,
                                        authority_ds=authority_ds,
                                        instance_ds=instance_ds,
                                        marc_record=record,
                                        creative_work_ds=creative_work_ds)
            ingester.ingest()
            if count%1000:
                if not count % 100:
                    sys.stderr.write(".")
            else:
                sys.stderr.write(str(count))

            count += 1
        end_time = datetime.datetime.now()
        sys.stderr.write("\nFinished at {0}\n".format(end_time.isoformat()))
        sys.stderr.write("Total time elapsed is {0} seconds\n".format((end_time-start_time).seconds))
        return count

def info():
    print("Current working directory {0}".format(os.getcwd()))
