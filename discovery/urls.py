"""
 mod:`urls` Discovery  App URL rounting
"""
__author__ = "Jeremy Nelson"

from django.conf.urls.defaults import *
import discovery.views

urlpatterns = patterns('discovery.views',
    url(r"$^", "app", name="discovery-default"),
    url(r"^authority/person/(\d+)/$", "person", name="discovery-authority-person"),
    url(r"^bibframe:Instance:(\d+)$", "instance", name="discovery-instance-direct"),
    url(r"^instance/(\d+)/$", "instance", name="discovery-instance"),
    url(r"^person/(\d+)/$", "person", name="discovery-person"),
    url(r"^bibframe:Work:(\d+)$", "creative_work", name="discovery-work-direct"),
    url(r"^work/(\d+)/$", "creative_work", name="discovery-work"),
    url(r"^facet/(\w+)/$", "facet_summary"),
    url(r"^facet/(\w+)/(\w+)/$", "facet_detail"),
)
