"""
 :mod:`models` MARC Batch app supporting models
"""
from django.db import models
from django.contrib.auth.models import User

class Job(models.Model):
    job_type = models.IntegerField(choices=[(0,'redis'),
                                            (1,'solr'),
                                            (2,'ils')],
                                   default=0)
    name = models.CharField(max_length=155)

class JobFeatures(models.Model):
    job = models.ForeignKey(Job)
    filename = models.CharField(max_length=255)
    name = models.CharField(max_length=155)

class JobLog(models.Model):
    creatd_on = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True,null=True)
    job = models.ForeignKey(Job)
    modified_marc = models.FileField(upload_to="modified",blank=True)
    original_marc = models.FileField(upload_to="uploads")

class ILSJobLog(JobLog):
    new_records = models.IntegerField(blank=True)
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
    
                        
    



    

