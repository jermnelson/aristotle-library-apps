from django.core.management.base import BaseCommand, CommandError
from aristotle.settings import REDIS_MASTER_HOST

class Command(BaseCommand)
    args = '<redis_host marc_file ...>'
    help = "Ingests a MARC21 binary file into the BIBFRAME Datastore"

    def handle(self, *args, **options):
        if redis_host not in args:
            redis_host = REDIS_MASTER_HOST
