"""
 mod:`url` MARC Batch App URL routing
"""
__author__ = 'Jeremy Nelson'
import marc_batch.views
from django.conf.urls.defaults import *

urlpatterns = patterns('marc_batch.views',
    url(r"^$","default",name='marc-batch-app-default'),
    url(r'^download$','download',name='marc-download'),
    url(r"^process$","job_process",name='marc-batch-job-process'),
    url(r"^ils/","ils",name='marc_batch-app-ils'),
    url(r"^jobs/(\d+)/$","job_display",name="marc_batch-job-display"),
    url(r"^redis/","redis",name='marc_batch-app-redis'),
    url(r"^solr/","solr",name='marc_batch_app_solr'),
    
)
                       
