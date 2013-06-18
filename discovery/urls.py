"""
 mod:`urls` Discovery  App URL rounting
"""
__author__ = "Jeremy Nelson"

from django.conf.urls.defaults import *
import discovery.views

urlpatterns = patterns('discovery.views',
    url(r"$^", "app", name="discovery-default"),
    url(r"^search$", "search", name="discovery-search"),
    url(r"^(\w+)/(\d+)/?$", "bibframe_router", name="discovery-bibframe-router"),
##    url(r"^authority/person/(\d+)/?$", "person", name="discovery-authority-person"),
##    url(r"^[c|C]over[A|_a]rt/(\d+)-(\w+).(\w+)$", "display_cover_image"),
##    url(r"^bibframe:Instance:(\d+)$", "instance", name="discovery-instance-direct"),
##    url(r"^[i|I]nstance/(\d+).json$", "instance_json_ld", name="discovery-instance-json_ld"),
##    url(r"^[i|I]nstance/(\d+)/?$", "instance", name="discovery-instance"),
##    url(r"^person/(\d+)/?$", "person", name="discovery-person"),
##    url(r"^person/(\d+).json$", "person_json_ld", name="discovery-person-json_ld"),
##    url(r"^bf:Work:(\d+)$", "creative_work", name="discovery-work-direct"),
##    url(r"^[w|W]ork/(\d+).json$", "creative_work_json_ld", name="discovery-work-json_ld"),
##    url(r"^[w|W]ork/(\d+)/?$", "creative_work", name="discovery-work"),
##    url(r"^[w|W]ork/(\d+)/?$", "creative_work", name="discovery-work"),
    url(r"^facet/([\w ]+)/$", "facet_summary"),
    url(r"^facet/([\w ]+)/([\w ]+)$", "facet_detail"),
)
