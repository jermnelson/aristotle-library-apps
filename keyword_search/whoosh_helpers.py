"Whoosh Helpers Module offers keyword searching for Bibframe entities in RLSP"
__author__ = "Jeremy Nelson"

import os
import urllib

from aristotle.settings import REDIS_DATASTORE, PROJECT_HOME

from django.template import Context, loader

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


def index_rdf_kw(**kwargs):
    """function indexes all elements in an XML RDF

    Keywords:
    indexer -- Whoosh indexer object, defaults to module INDEXER
    schema -- Whoosh Schema object, default to module's BF_SCHEMA
    work_key -- BIBFRAME Creative Work or subclass Redis key, defaults to None
    instance_keys -- List of BIBFRAME Instance keys
    author_keys -- List of BIBFRAME Author keys
    commit -- Boolean, default is True
    rdf_xml -- Lxml RDF object
    """
    indexer = kwargs.get('indexer', INDEXER)
    schema = kwargs.get('schema', BF_SCHEMA)
    rdf_xml = kwargs.get('rdf_xml')
    author_keys = kwargs.get('author_keys')
    commit = kwargs.get('commit', True)
    work_key = kwargs.get('work_key')
    instance_keys = kwargs.get('instance_key', [])
    title = kwargs.get('title')
    raw_content = u''
    
    for tags in rdf_xml.getroot().iter():
        if tags.text is None or len(tags.text) < 1:
            pass
        raw_content += u" {0}".format(tags.text)
    writer = indexer.writer()
    writer.add_document(instance_keys= u' '.join(instance_keys),
                        work_key=unicode(work_key, errors='ignore'),
                        title=unicode(title,
                                      errors='ignore'),
                        content=raw_content)
    if commit is True:
        writer.commit()
    


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
    output = {'hits' : []}
    indexer = kwargs.get('indexer', INDEXER)
    html_output = kwargs.get('html_output', True)
    page = kwargs.get('page', 1)
    query_text = kwargs.get('query_text', None)
    redis_datastore = kwargs.get('redis_datastore', REDIS_DATASTORE)
    schema = kwargs.get('schema', BF_SCHEMA)
    if query_text is None:
        raise ValueError('Keyword search query cannot be None')
    with indexer.searcher() as searcher:
        query = QueryParser("content", schema).parse(query_text)
        results = searcher.search_page(query, int(page), pagelen=5)
        output['page'] = page
        output['total'] = len(results)
        
        for i,hit in enumerate(results):
            fields = hit.fields()
            instance_info = {'title': fields.get('title')}
            work_key = fields.get('work_key')
            instance_info['workURL'] = "/apps/catalog/{0}".format(work_key)
            for instance_key in redis_datastore.smembers(
                '{0}:hasInstance'.format(work_key)):
                
                instance_info['instance_key'] = instance_key
                # Tries to extract cover image and holdings statement
                for annotation_key in redis_datastore.smembers(
                    '{0}:hasAnnotation'.format(instance_key)):
                    if annotation_key.startswith('bf:CoverArt'):
                        cover_id = annotation_key.split(":")[-1]
                        instance_info[
                            'coverURL'] = '/apps/catalog/CoverArt/{0}-body.jpg'.format(cover_id)
                    if annotation_key.startswith('bf:Holding'):
                        location_key = redis_datastore.hget(
                            annotation_key,
                            'schema:contentLocation')
                        location_label = redis_datastore.hget(
                                location_key,
                                'label')
                        location_url = redis_datastore.hget(
                                location_key,
                                'url')
                        if html_output:
                            holding_template = loader.get_template("find-in-library.html")
                            instance_info['instanceLocation'] = holding_template.render(
                                Context({'label': location_label,
                                         'url': location_label}))
                        else:
                            instance_info['instanceLocation'] = {
                                'label': location_label,
                                'url': location_url}
                if html_output:
                    item_detail_template = loader.get_template("item-details.html")
                    instance_info['instanceDetail'] = item_detail_template.render(
                        Context({'url': redis_datastore.hget(instance_key, 'url')}))
                else:
                    instance_info['instanceDetail'] = {
                        'url': redis_datastore.hget(instance_key, 'url')}
            if not 'coverURL' in instance_info:
                instance_info['coverURL'] = '/static/img/no-cover.png'
            output['hits'].append(instance_info)
                
                        
                
##            work_key_info = work_key.split(":")
##            instance_key = fields.get('instance_key')
##            fields['instance_thumbnail'] = redis_datastore.hget(
##                'bf:Work:icons',
##                'bf:{0}'.format(work_key_info[-2]))
##            if fields['instance_thumbnail'] is None:
##                fields['instance_thumbnail'] = redis_datastore.hget(
##                'bf:Work:icons',
##                'bf:Work')
##            fields['instance_thumbnail'] = '/static/img/{0}'.format(
##                fields['instance_thumbnail'])
##            fields['thumbnail_alt'] = 'Icon for {0}'.format(
##                fields.get('title'))
##            fields['work_url'] = '/apps/discovery/{0}/{1}'.format(
##                work_key_info[-2],
##                work_key_info[-1])
##            fields['work_summary'] = 'by '
##            for creator_key in redis_datastore.smembers(
##                '{0}:rda:isCreatorBy'.format(work_key)):
##                creator_key_info = creator_key.split(":")
##                fields['work_summary'] += """<a href="/apps/discovery/{0}/{1}">{2}</a>,
##""".format(creator_key_info[-2],
##           creator_key_info[-1],
##           redis_datastore.hget(creator_key,
##                                'rda:preferredNameForThePerson'))
##                                
##            hits.append(fields)
    return output
