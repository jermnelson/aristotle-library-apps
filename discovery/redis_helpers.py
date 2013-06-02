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
            'bf:Annotation:Facet:Formats',
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


class BIBFRAMESearch(object):

    def __init__(self,**kwargs):
        self.query = kwargs.get('q')
        self.type_of = kwargs.get('type_of', 'kw')
        self.annotation_ds = kwargs.get('annotation_ds', ANNOTATION_REDIS)
	self.authority_ds = kwargs.get('authority_ds', AUTHORITY_REDIS)
	self.creative_wrk_ds = kwargs.get('creative_wrk_ds', CREATIVE_WORK_REDIS)
        self.instance_ds = kwargs.get('instance_ds', INSTANCE_REDIS)
        self.operational_ds = kwargs.get('operational_ds', OPERATIONAL_REDIS)
        search_key = kwargs.get('search_key', None)
        if search_key is not None:
            # Checks to see if history key exists in datastore
            if not self.operational_ds.has_key(search_key):
                # Search key has expired set to None to create a new search
                # key
                search_key = None
            else:
                self.search_key = search_key
                # Reset search key expiration to 15 minutes
                self.operational_ds.expire(self.search_key, 900)
        if search_key is None:
            self.search_key = 'rlsp-query:{0}'.format(
                                   self.operational_ds.incr('global rlsp-query'))
            self.operational_ds.expire(self.search_key, 900)
	self.fails = []

    def __json__(self, with_results=True):
        """
        Method returns a json view of a BIBFRAMESearch

        Keywords:
        with_results -- Boolean, if True returns the search results in a list.
                        If False, just returns the number of creative work
                        keys 
        """
        info = {"query":self.query,
                "type": self.type_of,
                "query-key":self.search_key}
        if with_results is True: 
            info['works'] = list(self.operational_ds.smembers(self.search_key))
        else:
            info['works'] = self.operational_ds.scard(self.search_key)
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
        self.generate_facets()
        self.operational_ds.zadd('bibframe-searches', 
                                 time.time(),
                                 self.__json__(with_results=False))


    def author(self):
        found_creators = person_authority_app.person_search(self.query,
			                                    authority_redis=self.authority_ds)
        for work_key in found_creators:
             self.operational_ds.sadd(self.search_key,
                                      work_key)


    def creative_works(self):
        works = []
        for entity_key in self.operational_ds.smembers(self.search_key):
            # If entity is bf:Instance, get entity's Creative Work
            if entity_key.startswith('bf:Instance'):
                work_key = self.instance_ds.hget(entity_key, 'instanceOf')
            elif entity_key.startswith('bf:Work'):
                work_key = entity_key  
            works.append(Work(redis_key=work_key,
                              primary_redis=self.creative_work_ds))
        return works
        

    def generate_facets(self):
        facet_keys = ['bf:Annotation:Facet:formats',
                      'bf:Annotation:Facet:LOCFirstLetters:sort',
                      'bf:Annotation:Facet:Languages',
                      'bf:Annotation:Facet:PublicationDate']
        facets = {'Formats': { 'items':{}, 'count':0}}

        for format_key in self.annotation_ds.zrange('bf:Annotation:Facet:formats',
                                                    0,
                                                    -1):
            pass


    def journal_title(self):
        self.title()
        self.operational_ds.sinterstore(self.search_key, 
                                        self.search_key,
                                        'bf:Annotation:Facet:Format:Journal')



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
            self.operational_ds.sadd(self.search_key, key)



    def number_lccn(self):
        instance_key = self.instance_ds.hget('lccn-hash', self.query.strip())
        if instance_key is not None:
            self.operational_ds.sadd(self.search_key, instance_key)
        

    def number_med(self):
        instance_key = self.instance_ds.hget('nlm-hash', self.query.strip())
        if instance_key is not None:
            self.operational_ds.sadd(self.search_key, instance_key)
      

    def number_oclc(self):
        pass

    def subject_children(self):
        pass

    def subject_lc(self):
        pass

    def title(self):
        # Search using Title App
        found_titles = title_app.search_title(self.query,self.creative_wrk_ds)
        for title_key in found_titles:
            self.operational_ds.sadd(self.search_key,
                                     title_key)


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
        body_html = '<ul>'
        for i in xrange(1, 1 + int(RLSP_CLUSTER.get('global bf:Organization'))):
            org_key = 'bf:Organization:{0}'.format(i)
            body_html += '''<li>{0} Total Holdings={1}</li>'''.format(
                             RLSP_CLUSTER.hget(org_key, 'label'),
                             RLSP_CLUSTER.scard('{0}:bf:Holdings'.format(org_key)))
        body_html += '</ul>'
        item2 = {'heading': 'Institutional Collections',
                 'body': body_html}
        news.append(item2)
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




