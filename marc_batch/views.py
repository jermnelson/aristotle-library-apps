"""
 :mod:`views` Views for MARC Batch App
"""
__author__ = "Jeremy Nelson"

import os,sys
from django.views.generic.simple import direct_to_template
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.servers.basehttp import FileWrapper
from django.http import Http404,HttpResponse,HttpResponseRedirect
from aristotle.settings import INSTITUTION
from app_settings import APP
from marc_batch.fixures import help_loader
from models import Job,JobLog,ILSJobLog,job_types
from forms import *
import jobs.ils
import marc_helpers

def default(request):
    """
    Displays default view for the MARC Batch App
    """
    APP['view'] = 'default'
    ils_jobs,redis_jobs,solr_jobs = [],[],[]
    all_jobs = Job.objects.all().order_by('name')
    for job in all_jobs:
        if job.job_type == 1:
            redis_jobs.append(job)
        elif job.job_type == 2:
            solr_jobs.append(job)
        elif job.job_type == 3:
            ils_jobs.append(job)
    return direct_to_template(request,
                              'marc-batch-app.html',
                              {'app':APP,
                               'current_job': None,
                               'ils_jobs':ils_jobs,
                               'institution':INSTITUTION,
                               'redis_jobs':redis_jobs,
                               'solr_jobs':solr_jobs})
def download(request):
    """
    Download modified MARC21 file
    """
    if request.REQUEST.has_key("log_pk"):
        log_pk = request.REQUEST["log_pk"]
    else:
        log_pk = request.session['log_pk']
    record_log = ILSJobLog.objects.get(pk=log_pk)
    if request.REQUEST.has_key("original"):
        file_path = record_log.original_marc.path
    else:
        file_path = record_log.modified_marc.path  
    file_object = open(file_path,'r')
    file_wrapper = FileWrapper(file(file_path))
    filename = os.path.split(file_path)[1]
    response = HttpResponse(file_wrapper,content_type='text/plain')
    filename = os.path.split(file_path)[1]
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    response['Content-Length'] = os.path.getsize(file_path)
    return response

def ils(request):
    """
    Displays ils view for the MARC Batch App
    """
    APP['view'] = 'ils'
    ils_jobs = Job.objects.filter(job_type=3)
    return direct_to_template(request,
                              'marc_batch/ils.html',
                              {'app':APP,
                               'ils_jobs':ils_jobs,
                               'institution':INSTITUTION})

def ils_job_manager(request,job):
    """
    Helper function takes a Form's QueryDict and processes MARC file with specific
    rules

    :param request: HTTP reaquest
    :param job: Job object
    """
    ils_job_form = MARCRecordUploadForm(request.POST,request.FILES)
    ils_jobs = Job.objects.filter(job_type=3).order_by('name')
    if ils_job_form.is_valid():
        job_pk = request.POST['job_id']
        original_marc = request.FILES['raw_marc_record']
        job_query = Job.objects.get(pk=job_pk)
        params = {}
        ils_job_class = getattr(jobs.ils,'%s' % job_query.python_module)
        ils_job = ils_job_class(original_marc)
        ils_job.load()
        ils_log_entry = ILSJobLog(job=job_query,
                                  description=ils_job_form.cleaned_data['notes'],
                                  original_marc=original_marc,
                                  record_type=ils_job_form.cleaned_data['record_type'])
        ils_log_entry.save()
        ils_marc_output = ils_job.output()
        ils_log_entry.modified_marc.save('job-%s-%s-modified.mrc' % (job_query.name,
                                                                     ils_log_entry.created_on.strftime("%Y-%m-%d")),
                                         ContentFile(ils_marc_output))
        ils_log_entry.save()
        data = {'job':int(job_query.pk)}
        ils_log_form = ILSJobLogForm(data)
        request.session['log_pk'] = ils_log_entry.pk
        log_notes_form = JobLogNotesForm()
        return direct_to_template(request,
                                  'marc_batch/log.html',
                                  {'app':APP,
                                   'current_job':job_query,
                                   'current_log':ils_log_entry,
                                   'ils_jobs':ils_jobs,
                                   'log_form':ils_log_form,
                                   'log_notes_form':log_notes_form})
                
    else:
        print("Invalid form errors=%s" % ils_job_form.errors)
    
def job_display(request,job_pk):
    """
    Displays a Job form for MARC batch operation

    :param request: HTTP Request
    :param job_pk: Job's Django primary key
    """
    job_help = None
    template_filename = 'marc-batch-app.html'
    job = Job.objects.get(pk=job_pk)
    if job.help_rst is not None:
        job_help = {"title":job.name,
                    "contents":help_loader.get(job.help_rst)}
    for row in job_types:
        if row[0] == job.job_type:
            template_filename = '%s.html' % row[1]
    ils_jobs = Job.objects.filter(job_type=3).order_by('name')
    marc_form = MARCRecordUploadForm()
    return direct_to_template(request,
                              template_filename,
                              {'app':APP,
                               'current_job':job,
                               'help':job_help,
                               'ils_jobs':ils_jobs,
                               'institution':INSTITUTION,
                               'marc_upload_form':marc_form})

def job_history(request,job_pk):
    """
    Displays the history for a MARC batch job

    :param request: HTTP request
    :param job_pk: Django primary key for job
    """
    job = Job.objects.get(pk=job_pk)
    job_logs = JobLog.objects.filter(job=job).order_by("created_on")
    return direct_to_template(request,
                              'marc_batch/history.html',
                              {'app':APP,
                               'current_job':job,
                               'institution':INSTITUTION,
                               'logs':job_logs})
                               

def job_finished(request,job_log_pk):
    """
    Displays finished job

    :param request: HTTP Request
    :param job_log_pk: Job Log's primary key
    """
    job_log = JobLog.objects.get(pk=job_log_pk)
    return direct_to_template(request,
                              'marc_batch/finished.html',
                              {'app':APP,
                               'ils_jobs':Job.objects.filter(job_type=3).order_by('name'),
                               'institution':INSTITUTION,
                               'log_entry':job_log})

def job_process(request):
    """
    Takes submitted job from form and processes depending on
    the job type
    """
    if request.method != 'POST' or not request.POST.has_key('job_id'):
        raise Http404
    job = Job.objects.get(pk=request.POST['job_id'])
    if job.job_type == 1: # Redis Job
        pass
    elif job.job_type == 2: # Solr Job
        pass
    elif job.job_type == 3: # Legacy ILS Job
        return ils_job_manager(request,job)
    else:
        raise Http404
    return HttpResponseRedirect('/apps/marc_batch/finished')

def job_update(request):
    """
    Updates job log with results from external systems like legacy ILS

    :param request: HTTP request
    """
    if request.method != 'POST' or not request.POST.has_key('log_id'):
        raise Http404
    job = Job.objects.get(pk=request.POST['job_id'])
    if job.job_type == 1: # Redis Job
        pass
    elif job.job_type == 2: # Solr Job
        pass
    elif job.job_type == 3: # Legacy ILS JOB
        log = ILSJobLog.objects.get(pk=request.POST['log_id'])
        if request.POST.has_key("new_records"):
            new_records = request.POST['new_records']
            if len(new_records) > 0:
                log.new_records = new_records
        if request.POST.has_key('overlaid_records'):
            overlaid_records = request.POST['overlaid_records']
            if len(overlaid_records) > 0:
                log.overlaid_records = overlaid_records
        if request.POST.has_key('rejected_records'):
            rejected_records = request.POST['rejected_records']
            if len(rejected_records) > 0:
                log.rejected_records = rejected_records
        log.save()
    return HttpResponseRedirect('/apps/marc_batch/finished/{0}/'.format(log.pk))
        
            

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
                              
