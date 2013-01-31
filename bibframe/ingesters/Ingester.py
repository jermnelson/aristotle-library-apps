"""
 :mod:`ingesters` Module ingests MARC21 and MODS records into a MARCR-Redis datastore
 controlled by the MARCR app.
"""
__author__ = "Jeremy Nelson"

import datetime, re, pymarc, os, sys,logging, redis, time
from aristotle.settings import PROJECT_HOME
import json

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


class Ingester(object):
    """
    Base Ingester class for ingesting metadata and bibliographic
    records into the MARCR Redis datastore.
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
