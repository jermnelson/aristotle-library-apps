"""
 mod:`urls` BIBFRAME  App URL rounting
"""
__author__ = "Jeremy Nelson"

from django.conf.urls import *
import bibframe.views

urlpatterns = patterns('bibframe.views',
    url(r"$^","app",name="bibframe-default"),
    url(r"^annotation/(P<redis_key>\w)$","annotation",name="bibframe-annotation"),
    url(r"^authority/(P<redis_key>\w)$","annotation",name="bibframe-authority"),
    url(r"^creative_work/(P<redis_key>\w)$",
        "creative_work",
        name="bibframe-creative-work"),
    url(r"ingest$","ingest",name="bibframe-ingest"),
    url(r"^instance/(P<redis_key>\w)$",
        "instance",
        name="bibframe-instance"),
    url(r"manage$","manage",name="bibframe-manage"),
##    url(r"search$","search",name="bibframe-json"),
    url(r"^work/(P<redis_key>\w)$","creative_work",name="bibframe-work"),
)
