"""
 dbpedia_helpers.py

 Helper utilities for enchancing BIBFRAME entities
"""
__author__ = "Jeremy Nelson"

import json
import urllib2

from aristotle.settings import REDIS_DATASTORE

DBEDIA_DATA_URL = 'http://dbpedia.org/data/{0}.json'
DBEDIA_RESOURCE_URL = 'http://dbpedia.org/resource/{0}'

def enhance_authority(wiki_form,
                      rlsp_ds=REDIS_DATASTORE):
    """
    Function takes the wikipedia form of a name, queries dbpedia,
    and retrieves identifiers and other information about the authority

    Parameters:
    wiki_form -- Wiki form of name
    rlsp_ds -- Redis Datastore
    """
    output = {}
    dbpedia_json_url = urllib2.urlopen(DBEDIA_DATA_URL.format(wiki_form))
    if dbpedia_json_url.getcode() == 200:
        dbpedia_json = json.load(dbpedia_json_url)
    else:
        raise ValueError("Cannot retrieve {0}".format(
            DBEDIA_DATA_URL.format(wiki_form)))
    dbpedia_resource_url = urllib2.urlopen(DBEDIA_RESOURCE_URL.format(
        wiki_form))
    lccn_result = dbpedia_json.get(
        dbpedia_resource_url).get("http://dbpedia.org/property/lccn")
    if lccn_result is not None:
        output['lccn'] = []
        for row in lccn_result:
            lccn_raw = lccn.get('value').replace("n/","n")
            lccn_raw = lccn_raw.replace("/","0")
            output['lccn'].append(lccn_raw)
    viaf_result = dbpedia_json.get(
        dbpedia_resource_url).get("http://dbpedia.org/property/lccn")
    if viaf_result is not None:
        output['viaf'] = []
        for row in viaf_result:
            output['viaf'].append(row.get('value'))
    return output
