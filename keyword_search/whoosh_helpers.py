"Whoosh Helpers Module offers keyword searching for Bibframe entities in RLSP"
__author__ = "Jeremy Nelson"

import os

from aristotle.settings import REDIS_DATASTORE, PROJECT_HOME

from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import Schema, TEXT, KEYWORD, STORED
from whoosh.index import create_in
from whoosh.qparser import QueryParser

BF_SCHEMA = Schema(
    title=TEXT(stored=True),
    work_id=TEXT(stored=True),
    content=TEXT)
    

INDEXER = create_in(os.path.join(PROJECT_HOME,
                                 "keyword_search",
                                 "index"),
                    BF_SCHEMA)



def index_marc(**kwargs):
    """function indexes MARC21 file for BIBFRAME searching

    Keywords:
    indexer -- Whoosh indexer object, defaults to module INDEXER
    schema -- Whoosh Schema object, default to module's BF_SCHEMA
    redis_datastore -- RLSP datastore, defaults to Aristotle Settings
    work_key -- BIBFRAME Creative Work or subclass Redis key, defaults to None
    instance_keys -- List of BIBFRAME Instance keys
    annotation_keys -- List of BIBFRAME Annotation keys
    authority_keys -- List of BIBFRAME Authority keys
    commit -- Boolean, default is True
    """
    indexer = kwargs.get('indexer', INDEXER)
    schema = kwargs.get('schema', BF_SCHEMA)
    redis_datastore = kwargs.get('redis_datastore', REDIS_DATASTORE)
    marc_record = kwargs.get('record', None)
    work_key = kwargs.get('work_key', None)    
    instance_keys = kwargs.get('instance_keys', [])
    annotation_keys = kwargs.get('annotation_keys', [])
    authority_keys = kwargs.get('authority_keys', [])
    commit = kwargs.get('commit', True)
    raw_content = u''
    for field in marc_record:
        raw_content += u'{0} '.format(field.value())
    writer = indexer.writer()
    writer.add_document(title=unicode(marc_record.title(),
                                      errors='ignore'),
                        work_id=work_key,
                        content=raw_content)
    if commit is True:
        writer.commit()
                        
    
    
    
    
def keyword_search(**kwargs):
    """function performs a keyword search using a Whoosh search index

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
        query = QueryParser("content", schema).parse(unicode(query_text,
                                                             errors='ignore'))
        results = searcher.search(query)
        for hit in results:
            hits.append(hit.fields())
    return hits
