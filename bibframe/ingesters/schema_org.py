"""
 :mod:`schema_org` Module ingest a schema.org json-linked data or webpage into BIBFRAME Datastore
"""
__author__ = "Jeremy Nelson"

from bibframe.models import *
from bibframe.ingesters.Ingester import Ingester
from rdflib import RDF, RDFS, Namespace
import json



