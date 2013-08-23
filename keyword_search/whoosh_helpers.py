"Whoosh Helpers Module offers keyword searching for Bibframe entities in RLSP"
__author__ = "Jeremy Nelson"

import os

from aristotle.settings import REDIS_DATASTORE, PROJECT_HOME

from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import Schema, TEXT, KEYWORD, STORED, ID
from whoosh.index import create_in, open_dir, EmptyIndexError
from whoosh.qparser import QueryParser

BF_SCHEMA = Schema(
    author_keys = KEYWORD(stored=True),
    instance_keys = KEYWORD(stored=True),
    title = TEXT(stored=True),
    work_key = ID(stored=True),
    content = TEXT)
    
BF_INDEX_FILE_STORAGE = os.path.join(PROJECT_HOME,
                                     "keyword_search",
                                     "index")

if os.path.exists(BF_INDEX_FILE_STORAGE):
    try:
        INDEXER = open_dir(BF_INDEX_FILE_STORAGE)
    except EmptyIndexError:
        INDEXER = create_in(BF_INDEX_FILE_STORAGE,
                        BF_SCHEMA)
else:
    INDEXER = create_in(BF_INDEX_FILE_STORAGE,
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
    writer.add_document(instance_keys= u' '.join(instance_keys),
                        work_key=unicode(work_key, errors='ignore'),
                        title=unicode(marc_record.title(),
                                      errors='ignore'),
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
        query = QueryParser("content", schema).parse(query_text)
        results = searcher.search(query)
        for hit in results:
            fields = hit.fields()
            work_key = fields.get('work_key')
            work_key_info = work_key.split(":")
            instance_key = fields.get('instance_key')
            fields['instance_thumbnail'] = redis_datastore.hget(
                'bf:Work:icons',
                'bf:{0}'.format(work_key_info[-2]))
            if fields['instance_thumbnail'] is None:
                fields['instance_thumbnail'] = redis_datastore.hget(
                'bf:Work:icons',
                'bf:Work')
            fields['instance_thumbnail'] = '/static/img/{0}'.format(
                fields['instance_thumbnail'])
            fields['thumbnail_alt'] = 'Icon for {0}'.format(
                fields.get('title'))
            fields['work_url'] = '/apps/discovery/{0}/{1}'.format(
                work_key_info[-1],
                work_key_info[-2])
            fields['work_summary'] = 'by '
            for creator_key in redis_datastore.smembers(
                '{0}:rda:isCreatorBy'.format(work_key)):
                creator_key_info = creator_key.split(":")
                fields['work_summary'] += """<a href="/apps/discovery/{0}/{1}">{2}</a>,
""".format(creator_key_info[-2],
           creator_key_info[-1],
           redis_datastore.hget(creator_key,
                                'rda:preferredNameForThePerson'))
                                
            hits.append(fields)
    return hits
