"""
 ingest_marc is a Django management command that ingests a MARC21
 file into a BIBFRAME Redis datastore.
"""
__author__ = "Jeremy Nelson"

import sys
from django.core.management.base import BaseCommand, CommandError
from aristotle.settings import REDIS_DATASTORE
from bibframe.ingesters.MARC21 import *

def profile_run():
   run_ingestion('bibframe/fixures/pride-and-prejudice.mrc','192.168.189.128')

def run_ingestion(MARC21_filename):
    """Function runs the ingestions for all of the datastores

    Parameter:
    MARC21_filename -- Name and path to MARC21 file
    """
    if REDIS_DATASTORE is not None:
        ingest_marcfile(marc_filename=MARC21_filename,
                        redis_datastore=REDIS_DATASTORE)



class Command(BaseCommand):
    args = '<marc_file>'
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
        if len(args) != 1:
            raise CommandError("ingest_marc requres a marc_file")
        marc_file = args[0]
        run_ingestion(marc_file)
