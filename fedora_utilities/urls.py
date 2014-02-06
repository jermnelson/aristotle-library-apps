"""
 mod:`urls` Fedora Batch App URL rourting
"""
__author__ = "Jeremy Nelson"

<<<<<<< HEAD
from django.conf.urls import *
=======
try:
    from django.conf.urls.defaults import *
except ImportError:
    from django.conf.urls import *
>>>>>>> 4cae87f593b2bf2cc7704a73c5ec668a7d4a706b

urlpatterns = patterns('fedora_utilities.views',
    url(r"$^", "default", name="fedora-batch-default"),
    url(r"add_stub$", "add_stub_from_template", name="add-obj-template"),
    url(r"mover$","object_mover", name="pid-mover"),

    url(r"index$","index_solr"),
    url(r"ingest$","batch_ingest"),
)
