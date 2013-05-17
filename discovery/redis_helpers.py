"""
`mod`: redis_helpers - Redis Helpers for Discovery App
"""
import json
import time
from aristotle.settings import ANNOTATION_REDIS, AUTHORITY_REDIS, INSTANCE_REDIS
from aristotle.settings import CREATIVE_WORK_REDIS, OPERATIONAL_REDIS
try:
    from aristotle.settings import RLSP_CLUSTER
except ImportError, e:
    RLSP_CLUSTER = None
import person_authority.redis_helpers as person_authority_app
import title_search.redis_helpers as title_app

__author__ = "Jeremy Nelson"

class Facet(object):

    def __init__(self, **kwargs):
        self.redis_ds = kwargs.get('redis')
        self.items = kwargs.get('items',[])
        self.redis_keys = kwargs.get('keys')
        self.name = kwargs.get('name')

class FacetError(Exception):
    "Exception for errors with Facets"

    def __init__(self, message):
        "FacetError with message"
        self.value = message

    def __str__(self):
        "FacetError string representation"
        return repr(self.value)

class FacetItem(object):

    def __init__(self, **kwargs):
        self.redis_ds = kwargs.get('redis')
        if self.redis_ds is None:
            raise FacetError("FacetItem requires a Redis instance")
        self.redis_key = kwargs.get('key','bibframe:Annotation:Facet')
        self.count = 0
        if 'count' in kwargs:
            self.count = kwargs.get('count')
        else:
            if self.redis_ds.exists(self.redis_key):
                self.count = self.redis_ds.scard(self.redis_key)
        if 'name' in kwargs:
            self.name = kwargs.get('name')
        else:
            self.name = self.redis_key.split(":")[-1]
        self.children = kwargs.get('children',[])

class AccessFacet(Facet):

    def __init__(self, **kwargs):
        kwargs['name'] = 'Access'
        kwargs['items'] = [
            FacetItem(
                key='bibframe:Annotation:Facet:Access:In the Library',
                redis=kwargs['redis']),
            FacetItem(
                key='bibframe:Annotation:Facet:Access:Online',
                redis=kwargs['redis'])]
        super(AccessFacet, self).__init__(**kwargs)
        #self.location_codes = kwargs.get('location_codes',[])
        #for code in self.location_codes:
            #code_key = "bibframe:Annotation:Facet:Location:{0}".format(code)
            #child_facet = Facet(redis=self.redis_ds,
                #key=code_key,
                #name=self.redis_ds.hget('bibframe:Annotation:Facet:Locations',
                    #code))
            #self.items.append(child_facet)


class FormatFacet(Facet):

    def __init__(self, **kwargs):
        kwargs['name'] = 'Format'
        kwargs['items'] = []
        # Formats are sorted by number of instances
        format_item_keys = kwargs['redis'].zrevrange(
            'bibframe:Annotation:Facet:Formats',
            0,
            -1,
            withscores=True
            )
        for row in format_item_keys:
            kwargs['items'].append(
                FacetItem(count=row[1],
                    key=row[0],
                    redis=kwargs['redis']))
        super(FormatFacet, self).__init__(**kwargs)


class LCFirstLetterFacet(Facet):

    def __init__(self, **kwargs):
        kwargs['name'] = 'Call Number'
        kwargs['items'] = []
        lc_item_keys = kwargs['redis'].zrevrange(
            'bf:Annotation:Facet:LOCFirstLetters:sort',
            0,
            5,
            withscores=True
            )
        for row in lc_item_keys:
            redis_key = row[0]
            loc_key = redis_key.split(":")[-1]
            item_name = kwargs['redis'].hget(
                'bf:Annotation:Facet:LOCFirstLetters',
                loc_key)
            kwargs['items'].append(
                FacetItem(count=row[1],
                    key=redis_key,
                    name=item_name,
                    redis=kwargs['redis']))
        super(LCFirstLetterFacet, self).__init__(**kwargs)

class LocationFacet(Facet):

    def __init__(self, **kwargs):
        kwargs['name'] = 'Location'
        kwargs['items'] = []
        location_keys = kwargs['redis'].zrevrange(
            'bf:Annotation:Facet:Locations:sort',
            0,
            -1,
            withscores=True
            )
        for row in location_keys:
            redis_key = row[0]
            location_code = redis_key.split(":")[-1]
            #org_key = kwargs['redis'].hget(
            #    'bibframe:Annotation:Facet:Locations',
            #    location_code)
            #item_name = kwargs['authority_ds'].hget(org_key,
            #                                        'label')
            item_name = kwargs['redis'].hget('bf:Annotation:Facet:Locations',
                                             location_code)
            kwargs['items'].append(
                FacetItem(count=row[1],
                    key=redis_key,
                    name=item_name,
                    redis=kwargs['redis']))
        super(LocationFacet, self).__init__(**kwargs)


class ShardSearch(object):
    """Base Shard Search Class

    This class uses redis-shard python module and REDIS_SERVERS
    settings to create a shard search
    """

    def __init__(self, **kwargs):
        """Initializes a Redis Shard search object

        Keyword Arguments:
        q -- String query
        servers -- Listing of search servers
        """
        self.q = kwargs.get('q')
        self.client = RedisShardAPI(kwargs.get('servers', REDIS_SERVERS))
 


class BIBFRAMEShardSearch(ShardSearch):
    """BIBFRAME Shard Search

    Class uses    
    """
    search_types =  {'au': "Author",
                     'cs': "Children Subject",
                     'dw': "Dewey Call Number",
                     'gov': "Government Document Call Number",
                     'is': 'ISBN and ISSN',
                     'kw': 'Keyword',
                     'jt': 'Journal Title',
                     'lc': 'Library of Congress Subject Heading',
                     'lccn': "Library of Congress Call Number",
                     'med': "Medical Subject",
                     'medc': "Medical Call Number",
                     'oclc': "OCLC Number",
                     'ol': "Open Library Number", 
                     'title': "Title"}

    def __init__(self, **kwargs):
        """Initializes a BIBFRAMEShardSearch 

        Keyword Arguments:
        type_of -- Type of BIBFRAME search, should be in the list of 
                   search_types, defaults to kw
        """
        self.query_type = kwargs.get('type', "kw")
        self.creator_keys = []

    def run(self):
        "Runs the query on Shard Client based on query string and type"
        if self.query_type == "kw":
            self.author()
            self.title()
        elif self.query_type == "au":
            self.author()
        elif self.query_type == 'is':
            self.number_issn_isbn()
        elif self.query_type == "t":
            self.title()
        self.client.zadd('bibframe-searches', 
                         time.time(),
                         self.__json__(with_results=False))


    # Helper functions for specific types of searches
    def author(self):
        "Author search uses Person and Organization Apps for searching"
        self.creator_keys.extend(person_app.shard_search(self.query,
                                                         client=self.client))
        self.creator_keys.extend(organization_app.shard_search(self.query,
                                                               client=self.client))

    def number_issn_isbn(self):
        "Number search for ISSN and ISBN identifiers"
        instances_keys = []
        issn = self.client.hget('issn-hash', self.query.strip())
        if issn is not None:
            instance_keys.extend(issn)
        isbn = self.client.hget('issn-hash', self.query.strip())
        if isbn is not None:
            instance_keys.extend(isbn)
        for key in instance_keys:
            self.creative_works.extend(self.client.hget(key,
                                                        'isInstanceOf'))

    def title(self):
        "Title search uses the Creative Work titles"
        self.creator_keys.extend(title_app.shard_search(self.query,
                                                        self.creative_wrk_ds))

class BIBFRAMESearch(object):

    def __init__(self,**kwargs):
        self.query = kwargs.get('q')
        self.type_of = kwargs.get('type_of', 'kw')
	self.authority_ds = kwargs.get('authority_ds', AUTHORITY_REDIS)
	self.creative_wrk_ds = kwargs.get('creative_wrk_ds', CREATIVE_WORK_REDIS)
        self.instance_ds = kwargs.get('instance_ds', INSTANCE_REDIS)
        self.operational_ds = kwargs.get('operational_ds', OPERATIONAL_REDIS)
        if 'servers' in kwargs:
            self.shard_client = RedisShardAPI(kwargs.get('servers'), 
                                              REDIS_SERVERS)
        else:
            self.shard_client = None
	self.creative_work_keys, self.fails = [], []

    def __json__(self, with_results=True):
        """
        Method returns a json view of a BIBFRAMESearch

        Keywords:
        with_results -- Boolean, if True returns the search results in a list.
                        If False, just returns the number of creative work
                        keys 
        """
        info = {"query":self.query,
                "type": self.type_of}
        if with_results is True:
            info['works'] = list(set(self.creative_work_keys))
        else:
            info['works'] = len(set(self.creative_work_keys))
        return json.dumps(info) 


    def run(self):
        """
        Runs the search based on the search type. Adds json representation of 
        the query to a sorted-set based on the time.
        """
        if self.type_of == 'au':
            self.author()
        elif self.type_of == 'cs':
            self.subject_children()
        elif self.type_of == 'dw':
            self.number_dewey()
        elif self.type_of == 'is':
            self.number_issn_isbn()
        elif self.type_of == 'kw':
            self.keyword()
        elif self.type_of == 'jt':
            self.journal_title()
        elif self.type_of == 'lc':
            self.subject_lc()
        elif self.type_of == 'lccn':
            self.number_lccn()
        elif self.type_of == 'med':
            self.subject_med()
        elif self.type_of == 'medc':
            self.number_med()
        elif self.type_of == 't':
            self.title()
        self.operational_ds.zadd('bibframe-searches', 
                                 time.time(),
                                 self.__json__(with_results=False))
        self.creative_work_keys = set(self.creative_work_keys)


    def author(self):
        found_creators = person_authority_app.person_search(self.query,
			                                    authority_redis=self.authority_ds)
        self.creative_work_keys.extend(list(found_creators))

    def journal_title(self):
        pass

    def keyword(self):
        #! This should do a Solr search as the default
        self.author()
        self.title()
	
    
    def number_dewey(self):
        pass

    def number_issn_isbn(self):
        instances_keys = []
        issn = self.instance.hget('issn-hash', self.query.strip())
        if issn is not None:
            instance_keys.extend(issn)
        isbn = self.instance.hget('issn-hash', self.query.strip())
        if isbn is not None:
            instance_keys.extend(isbn)
        for key in instance_keys:
            self.creative_works


    def number_lccn(self):
        instance_key = self.instance_ds.hget('lccn-hash', self.query.strip())
        if instance_key is not None:
            self.creative_work_keys.append(self.instance_ds.hget(instance_key, 
                                                                 'instanceOf'))
        

    def number_med(self):
        instance_key = self.instance_ds.hget('nlm-hash', self.query.strip())
        if instance_key is not None:
            self.creative_work_keys.append(self.instance_ds.hget(instance_key, 
                                                                 'instanceOf'))
      

    def number_oclc(self):
        pass

    def subject_children(self):
        pass

    def subject_lc(self):
        pass

    def title(self):
        # Search using Title App
        found_titles = title_app.search_title(self.query,self.creative_wrk_ds)
        self.creative_work_keys.extend(found_titles)


def get_news():
    news = []
    # In demo mode, just create a news item regarding the
    # statistics of the RLSP_CLUSTER
    if RLSP_CLUSTER is not None:
        item = {'heading': 'Current Statistics for RLSP Cluster',
                'body': '''<p><strong>Totals:</strong>
Works={0}<br>Instances={1}<br>Person={2}</p>
<p>Number of keys={3}</p>'''.format(RLSP_CLUSTER.get('global bf:Work'),
                                    RLSP_CLUSTER.get('global bf:Instance'),
                                    RLSP_CLUSTER.get('global bf:Person'),
                                    RLSP_CLUSTER.dbsize())}
        news.append(item)
    return news
        

def get_facets(annotation_ds, authority_ds):
    """
    Helper Function returns a list of Facets

    :param annotation_ds: Annotation Datastore
    """
    facets = []
    facets.append(AccessFacet(redis=annotation_ds))
    facets.append(FormatFacet(redis=annotation_ds))
    facets.append(LocationFacet(authority_ds=authority_ds,
                                redis=annotation_ds))
    facets.append(LCFirstLetterFacet(redis=annotation_ds))

    return facets



def get_result_facets(work_keys):
    """
    Helper function takes a list of Creative Works keys and returns
    all of the facets associated with those entities.

    :param work_keys: Work keys
    """
    facets = []
    return facets




