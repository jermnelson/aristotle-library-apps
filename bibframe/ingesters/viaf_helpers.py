"""
  viaf_helpers.py

  Utilities for enchancing BIBFRAME entities using viaf.org web services
"""
__author__ = "Jeremy Nelson"

import json
import rdflib
import urllib
import urllib2

from aristotle.settings import REDIS_DATASTORE
from lxml import etree

VIAF_AUTOSUGGEST_BASE = 'http://viaf.org/viaf/AutoSuggest?query={0}'
VIAF_IDENTIFIER_BASE = 'http://www.viaf.org/viaf/{0}'

def enhance_authority(raw_name,
                      rlsp_ds=REDIS_DATASTORE):
    """
    Function takes a raw name, queries VIAF.org for VIAF id, and then
    queries for RDF record and returns a dictionary for ingesting into
    datastore.

    Parameters:
    raw_name -- Name of person or organization
    rlsp_ds -- Redis datastore
    """
    output = {}
    try:
        name_quoted = urllib.quote_plus(str(raw_name))
    except:
        name_quoted = raw_name.replace(" ", "+")
    viaf_autosuggest_url = urllib2.urlopen(
        VIAF_AUTOSUGGEST_BASE.format(name_quoted))
    if viaf_autosuggest_url.getcode() == 200:
        viaf_json = json.load(viaf_autosuggest_url)
    else:
        raise ValueError("Cannot retrieve {0}, http code={1}".format(
            VIAF_AUTOSUGGEST_BASE.format(urllib.quote_plus(raw_name)),
            viaf_autosuggest_url.getcode()))
    if 'result' in viaf_json:
        if viaf_json['result'] is not None and len(viaf_json['result']) > 0:
            # Harvests the first result
            first_result = viaf_json['result'][0]
            if 'lc' in first_result:
                output['lccn'] = first_result.get('lc')
            if 'viafid' in first_result:
                output['viaf'] = first_result.get('viafid')
            if 'term' in first_result:
                output['skos:prefLabel'] = first_result.get('term')
    return output
