"""
 :mod:`views` Views for MARC Batch App
"""
__author__ = "Jeremy Nelson"

from django.views.generic.simple import direct_to_template
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.servers.basehttp import FileWrapper
from django.http import Http404,HttpResponse,HttpResponseRedirect
from aristotle.settings import INSTITUTION
from app_settings import APP
from models import Job,job_types
from forms import *
import jobs.ils as ils
import marc_helpers

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
def download(request):
    """
    Download modified MARC21 file
    """
    log_pk = request.session['log_pk']
    record_log = ILSJobLog.objects.get(pk=log_pk)
    modified_file = open(record_log.modified_file.path,'r')
    file_wrapper = FileWrapper(file(record_log.modified_file.path))
    response = HttpResponse(file_wrapper,content_type='text/plain')
    filename = os.path.split(record_log.modified_file.path)[1]
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    response['Content-Length'] = os.path.getsize(record_log.modified_file.path)
    return response

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

def job_process(request):
    """
    Takes submitted job from form and processes depending on
    the job type
    """
    if request.method != 'POST' or not request.POST.has_key('job_id'):
        raise Http404
    job = Job.objects.get(pk=request.POST['job_id'])
    if job.job_type == 0: # Redis Job
        pass
    elif job.job_type == 1: # Solr Job
        pass
    elif job.job_type == 2: # Legacy ILS Job
        ils_job_manager(request,job)
    else:
        raise Http404
    return HttpResponseRedirect('/apps/marc_batch/finished')

def ils(request):
    """
    Displays ils view for the MARC Batch App
    """
    APP['view'] = 'ils'
    return direct_to_template(request,
                              'marc_batch/ils.html',
                              {'app':APP,
                               'institution':INSTITUTION})

def ils_job_manager(request,job):
    """
    Helper function takes a Form's QueryDict and processes MARC file with specific
    rules

    :param request: HTTP reaquest
    :param job: Job object
    """
    ils_job_form = MARCRecordUploadForm(request.POST,request.FILES)
    if ils_job_form.is_valid():
        job_pk = request.POST['job_id']
        job_query = Job.objects.get(pk=job_pk)
        marc_modifiers = marc_helpers.MARCModifier(request.FILES['raw_marc_record'])
    else:
        print("Invalid form errors=%s" % ils_job_form.errors)
    

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
                              
