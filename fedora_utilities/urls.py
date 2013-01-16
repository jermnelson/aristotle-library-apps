"""
 mod:`urls` Fedora Batch App URL rourting
"""
__author__ = "Jeremy Nelson"

import fedora_utilities.views
from django.conf.urls.defaults import *

urlpatterns = patterns('fedora_utilities.views',
    url(r"$^","default",name="fedora-batch-default"),
    url(r"mover$","object_mover",name="pid-mover"),
    url(r"index$","index_solr"),
    url(r"ingest$","batch_ingest"),
)
