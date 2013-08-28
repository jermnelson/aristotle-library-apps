"""initialize_rlsp module creates the supporting Redis keys used in Redis
Library Services Platform, including BIBFRAME, MARC21, MODS, Schema.org, and
other vocabularies and schemas as needed."""
__author__ = "Jeremy Nelson"

import datetime
import os
import sys
from aristotle.settings import REDIS_DATASTORE, PROJECT_HOME
from django.core.management.base import BaseCommand, CommandError
from lxml import etree
from rdflib import RDF, RDFS, Namespace

BF_ABSTRACT = Namespace('http://bibframe.org/model-abstract/')


def __initializeBIBFRAME():
    "Initializes all BIBFRAME Keys"
    print("Initializing BIBFRAME labels")
    bf_rdf = etree.parse(os.path.join(PROJECT_HOME,
                                      'bibframe',
                                      'fixures',
                                      'vocab.rdf'))
    rdfs_resources_elems = bf_rdf.findall("{{{0}}}Resource".format(RDFS))
    for row in rdfs_resources_elems:
        attribute_uri = row.attrib.get('{{{0}}}about'.format(RDF))
        attrib_name = os.path.split(attribute_uri)[-1]
        if not REDIS_DATASTORE.hexists('bf:vocab:labels',
                                       attrib_name):
            label = row.find('{{{0}}}label'.format(RDFS))
            REDIS_DATASTORE.hset('bf:vocab:labels',
                                 attrib_name,
                                 label.text)
            sys.stderr.write(".")
    print("\nFinished Initializing BIBFRAME labels")
    # Initializes Facets
            
    

def __initializeMARC():
    "Initializes all MARC Redis supportting keys"
    marc_rdf_files = ['00X.rdf',
                      '0XX.rdf',
                      '1XX.rdf',
                      '2XX.rdf',
                      '3XX.rdf',
                      '4XX.rdf',
                      '5XX.rdf']
    print("Initializing MARC labels")
    for marc_filename in marc_rdf_files:
        marc_rdf_file = os.path.join(PROJECT_HOME,
                                     'marc_batch',
                                     'fixures',
                                     marc_filename)
        marc_rdf = etree.parse(marc_rdf_file)
        
        all_descriptions = marc_rdf.findall("{{{0}}}Description".format(RDF))
        for description in all_descriptions:
            label = description.find('{{{0}}}label'.format(RDFS))
            if label is not None:
                raw_name = description.attrib.get('{{{0}}}about'.format(RDF))
                redis_key = 'marc:{0}'.format(os.path.split(raw_name)[-1][1:])
                if not REDIS_DATASTORE.hexists('marc:labels',
                                               redis_key):
                    REDIS_DATASTORE.hset('marc:labels',
                                         redis_key,
                                         label.text)
                    sys.stderr.write(".")
        print("\n\tFinished {0}".format(marc_filename))
    print("Finished Initializing MARC labels")
                
                                         
                
                
        
def __initializeMODS():
    "Initializes all MODS keys"
    pass

def __initializeSchemaOrg():
    "Initializes all Schema.org Redis Keys"
    pass

def InitializeEmptyRLSP():
    "Function initializes an empty Redis datastore"
    __initializeBIBFRAME()
    __initializeMARC()
    __initializeMODS()
    __initializeSchemaOrg()
    

class Command(BaseCommand):
    args = ''
    help = "Initializes an empty RLSP with supporting Redis Keys"

    def handle(self, *args, **options):
        datastore_size = REDIS_DATASTORE.dbsize()
        if datastore_size > 0:
            raise CommandError(
                "REDIS_DATASTORE must be empty, size is {0}".format(
                    datastore_size))
        InitializeEmptyRLSP()
