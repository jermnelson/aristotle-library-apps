"""
 :mod:`ingesters` Module ingests MARC21 and MODS records into a MARCR-Redis datastore
 controlled by the MARCR app.
"""
__author__ = "Jeremy Nelson"

import datetime, re, pymarc, os, sys,logging, redis, time
from aristotle.settings import PROJECT_HOME, REDIS_CLUSTER
import json
import rediscluster
try:
    import aristotle.settings as settings
    CREATIVE_WORK_REDIS = settings.CREATIVE_WORK_REDIS
    INSTANCE_REDIS = settings.INSTANCE_REDIS
    AUTHORITY_REDIS = settings.AUTHORITY_REDIS
    ANNOTATION_REDIS = settings.ANNOTATION_REDIS
    OPERATIONAL_REDIS = settings.OPERATIONAL_REDIS
except ImportError, e:
    redis_host = '0.0.0.0'
    CREATIVE_WORK_REDIS = redis.StrictRedis(port=6380)
    INSTANCE_REDIS = redis.StrictRedis(port=6381)
    AUTHORITY_REDIS = redis.StrictRedis(port=6382)
    ANNOTATION_REDIS = redis.StrictRedis(port=6383)
    OPERATIONAL_REDIS = redis.StrictRedis(port=6379)

HONORIFIC_PREFIXES = ['Ms',
 'Miss',
 'Mrs',
 'Mr',
 'Master',
 'Rev',
 'Fr',
 'Dr',
 'Atty',
 'Prof',
 'Hon',
 'Pres',
 'Gov',
 'Coach',
 'Ofc']

HONORIFIC_SUFFIXES = ['M.A.',
                      'M.S.',
                     'M.F.A.',
                     'LL.M',
                     'M.L.A.',
                     'M.B.A.',
                     'M.Sc',
                     'J.D.',
                     'M.D.',
                     'D.O.',
                     'Pharm.D.',
                     'Ph.D.',
                     'I',
                     'II',
                     'III',
                     'IV',
                     'V']

DATE_RE = re.compile(r"(\d+\w*)-*(\d*\w*)")
def personal_name_parser(name_string):
    """Function parses a name and returns a dict of names

    This function takes a personal name in the following format:
    Last name, first name middle name, YYYY-YYYY. See unit tests
    for different name variations that can be parsed with this
    function.
    
    Parameters:
    name_string -- Name String in standard bibliographic uniform
                   format
    """
    
    person = {'rda:preferredNameForThePerson': name_string}
    all_names = filter(lambda x: len(x) > 0,
                       [name.strip() for name in ' '.join(name_string.split(",")).split(" ")])
    person['schema:familyName'] = all_names.pop(0)
    remaining_names = []
    while len(all_names) > 0:
        name = all_names.pop(0)
        if HONORIFIC_PREFIXES.count(name) > 0:
            person['schema:honorificPrefix'] = name
        elif HONORIFIC_SUFFIXES.count(name) > 0:
            person['schema:honorificSuffix'] = name
        elif DATE_RE.search(name) is not None:
            dates = DATE_RE.search(name).groups()
            person['rda:dateOfBirth'] = dates[0]
            if len(dates) > 1:
                person['rda:dateOfDeath'] = dates[1]
        else:
            remaining_names.append(name)
    if len(remaining_names) > 0:
        person['schema:givenName'] = remaining_names.pop(0)
    if len(remaining_names) > 0:
        for row in remaining_names:
            if person.has_key('schema:additionalName'):
                person['schema:additionalName'] += ' {0}'.format(row)
            else:
                person['schema:additionalName'] = row
    return person

class Ingester(object):
    """
    Base Ingester class for ingesting metadata and bibliographic
    records into the BIBFRAME Redis datastore.
    """

    def __init__(self, **kwargs):
        """
        Initializes Ingester

        :keyword creative_work_ds: Work Redis datastore, defaults to
                                   CREATIVE_WORK_REDIS
        :keyword instance_ds: Instance Redis datastore, defaults to
                              INSTANCE_REDIS
        :keyword authority_ds: Authority Redis datastore, default to
                               AUTHORITY_REDIS
        :keyword annotation_ds: Annotation Redis datastore, defaults to
                                ANNOTATION_REDIS
        """
        self.annotation_ds = kwargs.get('annotation_ds',
                                        ANNOTATION_REDIS)
        self.authority_ds = kwargs.get('authority_ds',
                                       AUTHORITY_REDIS)
        self.instance_ds = kwargs.get('instance_ds',
                                      INSTANCE_REDIS)
        self.creative_work_ds = kwargs.get('creative_work_ds',
                                           CREATIVE_WORK_REDIS)

    def ingest(self):
        pass # Should be overridden by child classes

class ClusterIngester(object):
    "Base Ingester Class for a Redis Library Services Platform Cluster"

    def __init__(self, **kwargs):
        """Initializes Ingester

        Keyword arguements:
        cluster -- A dictionary of Redis Cluster instances, defaults to local
                   settings value
        """
        self.cluster = kwargs.get('cluster', REDIS_CLUSTER)
        if self.cluster is not None:
            self.cluster_ds = self.cluster
        else:
            self.cluster_ds = None
        

    def ingest(self):
        "Method stub, should be overriden by child classes"
        pass


