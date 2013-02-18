"""
 ingest_marc is a Django management command that ingests a MARC21
 file into a BIBFRAME Redis datastore.
"""
__author__ = "Jeremy Nelson"

import sys
from django.core.management.base import BaseCommand, CommandError
from aristotle.settings import *
from bibframe.ingesters import *

def profile_run():
   run_ingestion('bibframe/fixures/pride-and-prejudice.mrc','192.168.189.128')

def run_ingestion(MARC21_filename,
                  redis_host):
    """
    Function runs the ingestions for all of the datastores
    """
    if LOCAL is True:
        ingest_marcfile(marc_filename=MARC21_filename,
                        creative_work_redis=CREATIVE_WORK_REDIS,
                        instance_redis=INSTANCE_REDIS,
	                authority_redis=AUTHORITY_REDIS,
		        annotation_redis=ANNOTATION_REDIS)

    else:
        work_redis = redis.StrictRedis(host=redis_host, port=6380)
        instance_redis = redis.StrictRedis(host=redis_host, port=6381)
        authority_redis = redis.StrictRedis(host=redis_host, port=6382)
        annotation_redis = redis.StrictRedis(host=redis_host, port=6383)
        ingest_marcfile(marc_filename=MARC21_filename,
                        creative_work_redis=work_redis,
                        instance_redis=instance_redis,
		        authority_redis=authority_redis,
		        annotation_redis=annotation_redis)


class Command(BaseCommand):
    args = '<redis_host marc_file>'
    help = "Ingests a MARC21 binary file into the BIBFRAME Datastore"
##    option_list = BaseCommand.option_list + (
##        make_option('--redis_host',
##                    action='store_true',
##                    dest='redis_host',
##                    default=True,
##                    help='Redis host, default is {0}'.format(REDIS_MASTER_HOST)),
##        make_option('--marc_file',
##                    action='store_true',
##                    dest='marc_file',
##                    default=False,
##                    help='Path to MARC21 file')
##        )
        


    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError("ingest_marc requres a redis_host and marc_file")
        redis_host = args[0]
        marc_file = args[1]
        run_ingestion(marc_file,redis_host)
