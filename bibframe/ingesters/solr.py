"""
 mod:`solr` Indexes BIBFRAME entities into a Solr index
"""
__author__ = "Jeremy Nelson"
import datetime, os, sys, sunburnt
from bibframe.models import Annotation,Instance,Person,Organization,Work
import aristotle.settings as settings

BIBFRAME_SOLR = sunburnt.SolrInterface(settings.SOLR_URL)





