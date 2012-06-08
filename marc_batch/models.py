"""
 :mod:`models` MARC Batch app supporting models
"""
from django.db import models
from django.contrib.auth.models import User

job_types = [(1,'redis'),
             (2,'solr'),
             (3,'ils')]

marc_rec_types = [(1,"Bibliographic"),
                  (2,"Name Authority"),
                  (3,"Subject Authority")]

class Job(models.Model):
    job_type = models.IntegerField(choices=job_types,
                                   default=0)
    help_rst = models.CharField(max_length=50,
                                blank=True,
                                null=True)
    name = models.CharField(max_length=155)
    python_module = models.CharField(max_length=30,
                                     blank=True,
                                     null=True)
    

class JobFeatures(models.Model):
    job = models.ForeignKey(Job)
    filename = models.CharField(max_length=255)
    name = models.CharField(max_length=155)


class JobLog(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True,null=True)
    job = models.ForeignKey(Job)
    modified_marc = models.FileField(upload_to="modified",blank=True)
    original_marc = models.FileField(upload_to="uploads")
    record_type = models.IntegerField(blank=True,
                                      null=True,
                                      choices=marc_rec_types)

class JobLogNotes(models.Model):
    job = models.ForeignKey(JobLog)
    label = models.CharField(max_length=100, blank=True)
    note_value = models.TextField(blank=True)

class ILSJobLog(JobLog):
    load_table = models.IntegerField(null=True,blank=True)
    new_records = models.IntegerField(null=True,blank=True)
    overlaid_records = models.IntegerField(null=True,blank=True)
    rejected_records = models.IntegerField(null=True,blank=True)

class RedisJobLog(JobLog):
    expressions = models.IntegerField(blank=True,null=True)
    items = models.IntegerField(blank=True,null=True)
    manifestations = models.IntegerField(blank=True,null=True)
    works = models.IntegerField(blank=True,null=True)

class SolrJobLog(JobLog):
    records_indexed = models.IntegerField()
    end_time = models.TimeField(blank=True,null=True)
    start_time = models.TimeField()
    
                        
    



    

