"""
 :mod:`fabfile` Fabric File for Aristotle Library Apps Project deployment and 
 continous integration module
"""
__author__ = "Jeremy Nelson"
import os, sys
from fabric.api import local
from aristotle import settings

def ingest_shards_bibframe(location=".",
                           redis_host=settings.REDIS_MASTER_HOST):
    """
    Function takes a location to shards of MARC21 files and ingests into a
    the BIBFRAME Redis datastores.

    :param location: Location, defaults to current location
    """
    shard_walker = next(os.walk(location))[2]
    for filename in shard_walker:
        if os.path.splitext(filename)[1] == '.mrc':
            local('python manage.py ingest_marc {0} {1}'.format(redis_host,
                                                                os.path.join(location,filename)))
def test_all():
    local("./manage.py test")

def prepare_deploy():
    test_all()
