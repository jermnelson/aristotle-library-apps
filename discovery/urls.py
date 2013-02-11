"""
 mod:`urls` Discovery  App URL rounting
"""
__author__ = "Jeremy Nelson"

from django.conf.urls.defaults import *
import discovery.views

urlpatterns = patterns('discovery.views',
    url(r"$^", "app", name="discovery-default"),
    url(r"^authority/person/(\d+)/$", "person", name="discovery-authority-person"),
    url(r"^instance/(\d+)/$", "instance", name="discovery-instance"),
    url(r"^person/(\d+)/$", "person", name="discovery-person"),
    url(r"^work/(\d+)/$", "creative_work", name="discovery-work"),
)
