"""
 :mod:`views` Views for MARC Batch App
"""
__author__ = "Jeremy Nelson"

from django.views.generic.simple import direct_to_template
from django.http import HttpResponse
from aristotle.settings import INSTITUTION
from app_settings import APP
from models import Job,job_types
from forms import *

def default(request):
    """
    Displays default view for the MARC Batch App
    """
    APP['view'] = 'default'
    ils_jobs,redis_jobs,solr_jobs = [],[],[]
    all_jobs = Job.objects.all()
    for job in all_jobs:
        if job.job_type == 0:
            redis_jobs.append(job)
        elif job.job_type == 1:
            solr_jobs.append(job)
        elif job.job_type == 2:
            ils_jobs.append(job)
    return direct_to_template(request,
                              'marc-batch-app.html',
                              {'app':APP,
                               'ils_jobs':ils_jobs,
                               'institution':INSTITUTION,
                               'redis_jobs':redis_jobs,
                               'solr_jobs':solr_jobs})

def job_display(request,job_pk):
    """
    Displays a Job form for MARC batch operation

    :param request: HTTP Request
    :param job_pk: Job's Django primary key
    """
    template_filename = 'marc-batch-app.html'
    job = Job.objects.get(pk=job_pk)
    for row in job_types:
        if row[0] == job.job_type:
            template_filename = '%s.html' % row[1]
    marc_form = MARCRecordUploadForm()
    return direct_to_template(request,
                              template_filename,
                              {'app':APP,
                               'current_job':job,
                               'institution':INSTITUTION,
                               'marc_upload_form':marc_form})

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
                              
