"""
 loc_helpers.py

 Utilities for enchancing BIBFRAME entities using id.loc.gov web services
"""
__author__ = "Jeremy Nelson"

import json
import urllib2

from aristotle.settings import REDIS_DATASTORE

def get_uniform_name(lccn,
                     rlsp_ds=REDIS_DATASTORE):
    """
    Function takes a lccn, queries id.loc.gov and returns the preferred
    name for use in authority control.

    Parameters:
    lccn -- Library of Congress Control Number
    rlsp_ds -- Redis datastore
    """
    loc_json_raw_url = 'http://id.loc.gov/authorities/names/{0}.json'.format(
        lccn)
    loc_json_url = urllib2.urlopen(loc_json_raw_url)
    if loc_json_url.getcode() == 200:
        loc_json = json.load(loc_json_url)
    else:
        raise ValueError("Could not retrieve {0}, http code={1}".format(
            loc_json_raw_url,
            loc_json_url.getcode()))
    loc_authority_key = "<http://id.loc.gov/authorities/names/{0}>".format(
        lccn)
    if not loc_authority_key in loc_json:
        return
    loc_label_key = "<http://www.loc.gov/mads/rdf/v1#authoritativeLabel>"
    if loc_label_key in loc_json[loc_authority_key]:
        return loc_json[loc_authority_key][loc_label_key][0]['value']
        
    
