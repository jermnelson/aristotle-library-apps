"""
 mod:`solr` Indexes BIBFRAME entities into a Solr index
"""
__author__ = "Jeremy Nelson"
import datetime, os, sys, sunburnt
from bibframe.models import Annotation,Instance,Person,Organization,Work
import aristotle.settings as settings

BIBFRAME_SOLR = sunburnt.SolrInterface(settings.SOLR_URL)


def index_instance(instance,
                   annotation_ds=settings.ANNOTATION_REDIS,
                   authority_ds=settings.AUTHORITY_REDIS,
                   instance_ds=settings.INSTANCE_REDIS,
                   work_ds=settings.CREATIVE_WORK_REDIS):
    """
    Indexes a BIBFRAME Instance into a Solr index

    :param instance: BIBFRAME Instance
    :param annotation_ds: Default is settings.ANNOTATION_REDIS
    :param authority_ds: Default is settings.AUTHORITY_REDIS
    :param instance_ds: Default is settings.INSTANCE_REDIS
    :param work_ds: Default is settings.CREATIVE_WORK_REDIS)
 
    """
    solr_doc = {'id':instance.redis_key}
    for name,value in instance.feature().iteritems():
        if value is not None:
            solr_doc[name] = value   
    return solr_doc

def index_work(work,
               annotation_ds=settings.ANNOTATION_REDIS,
               authority_ds=settings.AUTHORITY_REDIS,
               instance_ds=settings.INSTANCE_REDIS,
               work_ds=settings.CREATIVE_WORK_REDIS):
    """
    Indexes a BIBFRAME Work into a Solr index

    :param work: BIBFRAME Work 
    :param annotation_ds: Default is settings.ANNOTATION_REDIS
    :param authority_ds: Default is settings.AUTHORITY_REDIS
    :param instance_ds: Default is settings.INSTANCE_REDIS
    :param work_ds: Default is settings.CREATIVE_WORK_REDIS)
 
    """
    solr_doc = {'id':work.redis_key}
    return solr_doc
