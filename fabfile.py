"""
 :mod:`fabfile` Fabric File for Aristotle Library Apps Project deployment and 
 continous integration module
"""
__author__ = "Jeremy Nelson"
import os, sys
from fabric.api import local

def ingest_shards_bibframe(location="."):
    """
    Function takes a location to shards of MARC21 files and ingests into a
    the BIBFRAME Redis datastores.

    :param location: Location, defaults to current location
    """
    shard_walker = next(os.walk(location))[2]
    for filename in shard_walker:
        file_ext = os.path.splitext(filename)[1]
        if  file_ext == '.marc' or file_ext == '.mrc':
            local('python manage.py ingest_marc {0}'.format(
                os.path.join(location,filename)))
def test_all():
    local("./manage.py test")

def prepare_deploy():
    test_all()
