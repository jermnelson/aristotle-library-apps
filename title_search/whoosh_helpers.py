__author__ = "Jeremy Nelson"

import datetime
import os

from aristotle.settings import REDIS_DATASTORE, PROJECT_HOME
from bibframe.ingesters.MARC21 import MARC21toTitleEntity

from whoosh.fields import Schema, TEXT, KEYWORD, STORED, ID
from whoosh.index import create_in, open_dir, EmptyIndexError

TITLE_SCHEMA = Schema(
    title_key = ID(stored=True),
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

def index_marc(**kwargs):
    """function indexes title information from either MARC authority or
    bibliogrpahic record"""
    indexer = kwargs.get('indexer', INDEXER)
    marc_record = kwargs.get('record', None)
    redis_datastore = kwargs.get('redis_datastore', REDIS_DATASTORE)
    schema = kwargs.get('schema', TITLE_SCHEMA)
    ingester = MARC21toTitleEntity(redis_datastore=redis_datastore,
                                   record=marc_record)
    ingester.ingest()
    if ingester.title_entity is None:
        # Failed to ingest, return without indexing
        return
    raw_content = u''
    for tag in ['130', '210', '222', '245', '246', '247', '730', '830']:
        fields = marc_record.get_fields(tag)
        for field in fields:
            raw_content += unicode(field.value(),
                                   errors='ignore')
    writer = indexer.writer()
    writer.add_document(title_key=unicode(ingester.title_entity.redis_key),
                        content=raw_content)
    writer.commit()
    
    
                                   
