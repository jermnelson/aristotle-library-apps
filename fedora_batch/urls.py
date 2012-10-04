"""
 mod:`urls` Fedora Batch App URL rourting
"""
__author__ = "Jeremy Nelson"

from django.conf.urls.defaults import *

urlpatterns = patterns('fedora_batch.views',
    url(r"$^","default",name="fedora-batch-default"),
    url(r"mover$","object_mover",name="pid-mover"),
)
