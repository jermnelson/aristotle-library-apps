__author__ = "Jeremy Nelson"

import datetime
import os

from aristotle.settings import REDIS_DATASTORE, PROJECT_HOME

from whoosh.fields import Schema, TEXT, KEYWORD, STORED, ID
from whoosh.index import create_in, open_dir, EmptyIndexError
from whoosh.qparser import QueryParser

PERSON_SCHEMA = Schema(
    person_key = ID(stored=True),
    name = TEXT(stored=True),
    content=TEXT)

PERSON_INDEX_FILE_STORAGE = os.path.join(
    PROJECT_HOME,
    "person_authority",
    "index")

if os.path.exists(PERSON_INDEX_FILE_STORAGE):
    try:
        INDEXER = open_dir(PERSON_INDEX_FILE_STORAGE)
    except EmptyIndexError:
        INDEXER = create_in(
            PERSON_INDEX_FILE_STORAGE,
            PERSON_SCHEMA)


def index_marc(**kwargs):
    """Function indexes Person information from MARC21 records"""
    indexer = kwargs.get('indexer', INDEXER)
    marc_record = kwargs.get('record', None)
    redis_datastore = kwargs.get('redis_datastore', REDIS_DATASTORE)
    schema = kwargs.get('schema', TITLE_SCHEMA)
    
