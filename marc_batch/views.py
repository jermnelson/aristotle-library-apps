"""
 :mod:`views` Views for MARC Batch App
"""
__author__ = "Jeremy Nelson"

from django.views.generic.simple import direct_to_template
from django.http import HttpResponse
from app_settings import APP
from settings import INSTITUTION

def default(request):
    """
    Displays default view for the MARC Batch App
    """
    APP['view'] = 'default'
    return direct_to_template(request,
                              'marc_batch/marc-batch-app.html',
                              {'app':APP,
                               'institution':INSTITUTION})

def ils(request):
    """
    Displays ils view for the MARC Batch App
    """
    APP['view'] = 'ils'
    return direct_to_template(request,
                              'marc_batch/ils.html',
                              {'app':APP,
                               'institution':INSTITUTION})


def redis(request):
    """
    Displays ils view for the MARC Batch App
    """
    APP['view'] = 'redis'
    return direct_to_template(request,
                              'marc_batch/redis.html',
                              {'app':APP,
                               'institution':INSTITUTION})

def solr(request):
    """
    Displays ils view for the MARC Batch App
    """
    APP['view'] = 'solr'
    return direct_to_template(request,
                              'marc_batch/solr.html',
                              {'app':APP,
                               'institution':INSTITUTION})    
                              
