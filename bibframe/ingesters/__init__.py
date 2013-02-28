"""
 :mod:`ingesters` Module ingests MARC21 and MODS records into a MARCR-Redis datastore
 controlled by the MARCR app.
"""
__author__ = "Jeremy Nelson"

import datetime, re, pymarc, os, sys,logging, redis, time
from bibframe.models import Annotation, Organization, Work, Instance, Person
from call_number.redis_helpers import generate_call_number_app
from person_authority.redis_helpers import get_or_generate_person
from aristotle.settings import PROJECT_HOME
from title_search.redis_helpers import generate_title_app,search_title
import marc21_facets
from MARC21 import MARC21toBIBFRAME
from lxml import etree
from rdflib import RDF,RDFS,Namespace
import json

STD_SOURCE_CODES = json.load(open(os.path.join(PROJECT_HOME,
                                               'bibframe',
                                               'fixures',
                                               'standard-id-src-codes.json'),
                                  'rb'))

BF = Namespace('http://bibframe.org/model-abstract/')


def info():
    print("Current working directory {0}".format(os.getcwd()))
