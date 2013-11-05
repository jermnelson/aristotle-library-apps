"""
 powells_helpers.py

 Extracts Book metadata information from api.powells.com, an API service from
 Powell's books.
"""
__author__ = "Jeremy Nelson"

import json
import urllib
import urllib2

from aristotle.settings import REDIS_DATASTORE
from bibframe.models import CoverArt

POWELLS_API = 'http://api.powells.com/v0d/testing/search/{0}.data'


def cover_art_from_title(title,
                         rlsp_ds=REDIS_DATASTORE):
    """
    Helper function takes a title string and Redis datastore,
    attempts to download json for the title from api.powells.com
    and if cover_id exists for the first item, attempts to
    download and save thumbnails

    Parameters:
    title -- raw title string
    rlsp_ds -- Redis datastore, default is REDIS_DATASTORE setting
    """
    annotationBody, thumbnail = None, None
    search_url = POWELLS_API.format(urllib.quote_plus(title))
    

