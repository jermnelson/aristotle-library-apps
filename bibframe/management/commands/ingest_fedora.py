"""
 ingest_fedora_mods is a Django management command for ingesting various types of
Fedora Commons' MODS records into the Redis Library Services Platform
"""
__author__ = "Jeremy Nelson"

import datetime
import os
import sys
from aristotle.settings import REDIS_DATASTORE, FEDORA_URI, FEDORA_ROOT
from aristotle.settings import FEDORA_USER, FEDORA_PASSWORD


FEDORA_REPO = Repository(root=FEDORA_ROOT,
                         username=FEDORA_USER,
                         password=FEDORA_PASSWORD)

from bibframe.ingesters.ProjectGutenbergRDF import ProjectGutenbergIngester
from django.core.management.base import BaseCommand, CommandError


PREFIX_HASH_KEY = 'carl-adr-prefixes'

def ingest_fedora(parent_pid):
    """Function ingests a collection of Fedora Commons objects into the
    BIBFRAME Redis datastore

    Parameters:
    parent_pid -- PID of Parent Collection
    """
    collection_sparql = """PREFIX fedora: <info:fedora/fedora-system:def/relations-external#>
SELECT ?a FROM <#ri> WHERE {
   ?a <info:fedora/fedora-system:def/relations-external#isMemberOfCollection>"""
    collection_sparql += "<info:fedora/{0}>".format(parent_pid) +  "}"
    ingester = MODSIngester(redis_datastore=REDIS_DATASTORE)
    csv_reader = FEDORA_REPO.risearch.sparql_query(collection_sparql)
    collection_pids = []
    for row in csv_reader:
        full_pid = row.get('a')
        collection_pids.append(full_pid.split("/")[-1])
    start_time = datetime.datetime.utcnow()
    sys.stderr.write("Started Fedora Commons Object Ingestion at {0}\n".format(
        start_time.isoformat()))
    for pid in collection_pids:
        repo_mods_result = FEDORA_REPO.api.getDatastreamDissemination(
            pid=pid,
            dsID="MODS")
        ingester.mods_xml = repo_mods_result[0]
        ingester.__ingest__()
        thumbnail_result = FEDORA_REPO.api.getDatastreamDissemination(
            pid=pid,
            dsID="TN")
        org_key = REDIS_DATASTORE.hget(PREFIX_HASH_KEY,
                                       pid.split(":")[0])
        for instance_key in self.instances:
            if thumbnail_result is not None:
                new_cover = CoverArt(redis_datastore=redis_datastore,
                                     annotates=instance_key)
                setattr(new_cover,
                        'prov:generated',
                        FEDORA_URI)
                setattr(new_cover,
                        'thumbnail',
                        thumbnail_result)
                new_cover.save()
                REDIS_DATASTORE.sadd('{0}:hasAnnotation'.format(instance_key),
                                     new_cover.redis_key)
            if org_key is not None:
                REDIS_DATASTORE.sadd('{0}:resourceRole:own'.format(org_key),
                                     instance_key)
                
                
                
            
            
    
    
    end_time = datetime.datetime.utcnow()
    sys.stderr.write("Finished Fedora Commons Object Ingestion at {0} ".format(
        end_time.isoformat()))
    sys.stderr.write("Total Objects processed={0} time={1} minutes".format(
        len(collection_pids),
        (end_time-start_time).seconds / 60.0))
  
   
class Command(BaseCommand):
    args = '<parent_pid>'
    help = "Ingests Fedora Commons Objects into the BIBFRAME Datastore"

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("ingest_rdf requires the parent pid")
        parent_pid = args[0]
        ingest_fedora(parent_pid)
        
                  
