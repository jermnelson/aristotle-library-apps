"""
 ingest_rdf is a Django management command for ingesting various types of RDF 
 records into BIBFRAME Redis datastore
"""
__author__ = "Jeremy Nelson"

import datetime
import os
import sys
from aristotle.settings import ANNOTATION_REDIS, AUTHORITY_REDIS
from aristotle.settings import CREATIVE_WORK_REDIS, INSTANCE_REDIS
from bibframe.ingesters.ProjectGutenbergRDF import ProjectGutenbergIngester
from django.core.management.base import BaseCommand, CommandError


# Types of supported RDF ingestion, currently only Project Gutenberg
# RDF files
RDF_TYPES = ['pg']

def ingest_pg_rdfs(rdf_filepath):
    """
    Function ingests a Project Gutenberg RDF files into the BIBFRAME Redis 
    datastore

    :param rdf_filepath: Full path to the Project Gutenberg RDF XML files
    """
    ingester = ProjectGutenbergIngester(annotation_ds=ANNOTATION_REDIS,
                                        authority_ds=AUTHORITY_REDIS,
                                        creative_work_ds=CREATIVE_WORK_REDIS,
                                        instance_ds=INSTANCE_REDIS)
    rdf_walk_results = next(os.walk(rdf_filepath))
    start_time = datetime.datetime.utcnow()
    sys.stderr.write("Started Project Gutenberg Ingestion at {0}\n".format(
        start_time.isoformat()))
    counter = 0
    for filename in rdf_walk_results[2]:
        if filename.endswith(".rdf"):
            try:
                ingester.ingest(os.path.join(rdf_filepath,
                                             filename))
            except:
                print("Error {0} ingesting {1}".format(sys.exc_info()[0],
                                                       filename))
            if not counter%100:
                sys.stderr.write(".")
            if not counter%1000:
                sys.stderr.write(" {0}:{1} ".format(filename, counter))
        counter += 1
    end_time = datetime.datetime.utcnow()
    sys.stderr.write("Finished Project Gutenberg Ingestion at {0} ".format(
        end_time.isoformat()))
    sys.stderr.write("Total RDF files processed={0} time={1} minutes".format(
        counter,
        (end_time-start_time).seconds / 60.0))
  
   
class Command(BaseCommand):
    args = '<rdf_filepath rdf_type>'
    help = "Ingests rdf files of a specific type into the BIBFRAME Datastore"

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError("ingest_rdf requires rdf files path and type")
        rdf_filepath = args[0]
        rdf_type = args[1]
        if RDF_TYPES.count(rdf_type) < 1:
            raise CommandError("RDF type {0} not in {1}".format(rdf_type,
                                                                RDF_TYPES))
        if rdf_type == 'pg':
            ingest_pg_rdfs(rdf_filepath)
                  
