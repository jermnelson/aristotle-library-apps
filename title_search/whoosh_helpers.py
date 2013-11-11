__author__ = "Jeremy Nelson"

import datetime
import os

from aristotle.settings import REDIS_DATASTORE, PROJECT_HOME
from bibframe.ingesters.MARC21 import MARC21toTitle

from whoosh.fields import Schema, TEXT, KEYWORD, STORED, ID
from whoosh.index import create_in, open_dir, EmptyIndexError
from whoosh.qparser import QueryParser

TITLE_SCHEMA = Schema(
    title_key = ID(stored=True),
    uniform_title = TEXT(stored=True),
    content = TEXT)

TITLE_INDEX_FILE_STORAGE = os.path.join(
    PROJECT_HOME,
    "title_search",
    "index")

if os.path.exists(TITLE_INDEX_FILE_STORAGE):
    try:
        INDEXER = open_dir(TITLE_INDEX_FILE_STORAGE)
    except EmptyIndexError:
        INDEXER = create_in(
            TITLE_INDEX_FILE_STORAGE,
            TITLE_SCHEMA)
else:
    INDEXER = create_in(
        TITLE_INDEX_FILE_STORAGE,
        TITLE_SCHEMA)

def index_title_entity(**kwargs):
    """Function indexes title information from a titleEntity
    """
    indexer = kwargs.get('indexer', INDEXER)
    title_key = kwargs.get('title_key')
    redis_datastore = kwargs.get('redis_datastore', REDIS_DATASTORE)
    raw_content = u''
    for value in redis_datastore.hvals(title_key):
        raw_content += u" {0}".format(value)
    if redis_datastore.exists("{0}:rda:variantTitle".format(
        title_key)):
        for title in redis_datastore.smembers(
            "{0}:rda:variantTitle".format(title_key)):
            raw_content += u" {0}".format(title)
    writer = indexer.writer()
    writer.add_document(title_key=unicode(title_key),
                        content=raw_content)
    writer.commit()

def index_marc(**kwargs):
    """function indexes title information from either MARC authority or
    bibliographic record"""
    indexer = kwargs.get('indexer', INDEXER)
    marc_record = kwargs.get('record', None)
    redis_datastore = kwargs.get('redis_datastore', REDIS_DATASTORE)
    schema = kwargs.get('schema', TITLE_SCHEMA)
    ingester = MARC21toTitle(redis_datastore=redis_datastore,
                             record=marc_record)
    ingester.ingest()
    if ingester.title_entity is None:
        # Failed to ingest, return without indexing
        return
    else:
        index_title_entity(title_key=ingester.title_entity,
                           indexer=indexer,
                           redis_datastore=redis_datastore)
##    if marc_record['130'] is not None:
##        uniform_title = ' '.join(
##            [field.value() for field in marc_record.get_fields('130')])
##    else:
##        uniform_title = u''
##    raw_content = u''
##    for tag in ['130', '210', '222', '245', '246', '247', '430', '730', '830']:
##        fields = marc_record.get_fields(tag)
##        for field in fields:
##            raw_content += field.value()
####            raw_content += unicode(field.value(),
####                                   errors='ignore')
##    writer = indexer.writer()
##    writer.add_document(title_key=unicode(ingester.title_entity.redis_key),
##                        content=raw_content,
##                        uniform_title=uniform_title)
##    writer.commit()

def title_search(**kwargs):
    """function takes a number args and search title indexer

    Keywords:
    indexer -- Whoosh indexer object, defaults to module INDEXER
    schema -- Whoosh Schema object, default to module's BF_SCHEMA
    redis_datastore -- RLSP datastore, defaults to Aristotle Settings
    query_text -- Text to search on
    """
    hits = []
    indexer = kwargs.get('indexer', INDEXER)
    schema = kwargs.get('schema', BF_SCHEMA)
    redis_datastore = kwargs.get('redis_datastore', REDIS_DATASTORE)
    query_text = kwargs.get('query_text', None)
    if query_text is None:
        raise ValueError('Keyword search query cannot be None')
    with indexer.searcher() as searcher:
        query = QueryParser("content", schema).parse(query_text)
        results = searcher.search(query)
        for hit in results:
            fields = hit.fields()
            title_key = fields.get('title_key')
            uniform_title = fields.get('uniform_title')
            hits.append((title_key, uniform_title))
    return hits
    
            
    
    
                                   
