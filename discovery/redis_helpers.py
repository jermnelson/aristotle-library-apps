"""
`mod`: redis_helpers - Redis Helpers for Discovery App
"""
__author__ = "Jeremy Nelson"
import json
import time
from aristotle.settings import REDIS_DATASTORE, OFFSET
from bibframe.models import CREATIVE_WORK_CLASSES
from django.template.defaultfilters import slugify
import person_authority.redis_helpers as person_authority_app
import title_search.redis_helpers as title_app

import bibframe.models

def slug_to_title(key):
    slug_name = key.split(":")[-1].replace("-"," ")
    slug_name = slug_name.title()
    slug_name = slug_name.replace('Vhs', 'VHS')
    slug_name = slug_name.replace('Dvd', "DVD")
    slug_name = slug_name.replace("Cd", "CD-")
    return slug_name

class Facet(object):

    def __init__(self, **kwargs):
        self.redis_ds = kwargs.get('redis')
        self.items = kwargs.get('items',[])
        self.redis_id = kwargs.get('redis_id')
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
        self.redis_key = kwargs.get('key', 'bf:Facet')
        self.count = 0
        if 'count' in kwargs:
            self.count = kwargs.get('count')
        else:
            if self.redis_ds.exists(self.redis_key):
                self.count = self.redis_ds.scard(self.redis_key)
        if 'name' in kwargs:
            self.name = kwargs.get('name')
        else:
            self.name = self.redis_ds.hget('bf:Facet:labels',
                                           self.redis_key)
        self.children = kwargs.get('children', [])

class AccessFacet(Facet):

    def __init__(self, **kwargs):
        kwargs['redis_id'] = 'access'
        
        kwargs['name'] = kwargs['redis'].hget('bf:Facet:labels',
                                              'bf:Facet:{0}'.format(
                                                      kwargs['redis_id']))
        kwargs['items'] = [
            FacetItem(
                key='bf:Facet:access:in-the-library',
                redis=kwargs['redis']),
            FacetItem(
                key='bf:Facet:access:online',
                redis=kwargs['redis'])]
        super(AccessFacet, self).__init__(**kwargs)
        #self.location_codxes = kwargs.get('location_codes',[])
        #for code in self.location_codes:
            #code_key = "bibframe:Annotation:Facet:Location:{0}".format(code)
            #child_facet = Facet(redis=self.redis_ds,
                #key=code_key,
                #name=self.redis_ds.hget('bibframe:Annotation:Facet:Locations',
                    #code))
            #self.items.append(child_facet)


class FormatFacet(Facet):

    def __init__(self, **kwargs):
        kwargs['redis_id'] = 'format'
        kwargs['name'] = kwargs.get('redis').hget('bf:Facet:labels',
                                                  'bf:Facet:{0}'.format(
                                                      kwargs['redis_id']))
        kwargs['items'] = []
        # Formats are sorted by number of instances
        format_item_keys = kwargs['redis'].zrevrange(
            'bf:Facet:format:sort',
            0,
            -1,
            withscores=True
            )
        for row in format_item_keys:
            kwargs['items'].append(
                FacetItem(count=int(row[1]),
                    key=row[0],
                    redis=kwargs['redis']))
        super(FormatFacet, self).__init__(**kwargs)


class LanguageFacet(Facet):

    def __init__(self, **kwargs):
        kwargs['redis_id'] = 'language'
        kwargs['name'] = kwargs['redis'].hget(
            'bf:Facet:labels',
            'bf:Facet:{0}'.format(kwargs['redis_id']))
        kwargs['items'] = []
        language_keys = kwargs['redis'].zrevrange(
            'bf:Facet:language:sort',
            0,
            5,
            withscores=True
            )
        for row in language_keys:
            redis_key = row[0]
            item_name = kwargs['redis'].hget(
                'bf:Facet:labels',
                redis_key)
            kwargs['items'].append(
                FacetItem(count=int(row[1]),
                    key=redis_key,
                    name=item_name,
                    redis=kwargs['redis']))
        super(LanguageFacet, self).__init__(**kwargs)

class LCFirstLetterFacet(Facet):

    def __init__(self, **kwargs):
        kwargs['redis_id'] = 'loc-first-letter'
        kwargs['name'] = kwargs['redis'].hget(
            'bf:Facet:labels',
            'bf:Facet:{0}'.format(kwargs['redis_id']))
        kwargs['items'] = []
        lc_item_keys = kwargs['redis'].zrevrange(
            'bf:Facet:loc-first-letter:sort',
            0,
            5,
            withscores=True
            )
        for row in lc_item_keys:
            redis_key = row[0]
            item_name = kwargs['redis'].hget(
                'bf:Facet:labels',
                redis_key)
            kwargs['items'].append(
                FacetItem(count=int(row[1]),
                    key=redis_key,
                    name=item_name,
                    redis=kwargs['redis']))
        super(LCFirstLetterFacet, self).__init__(**kwargs)

class LocationFacet(Facet):

    def __init__(self, **kwargs):
        kwargs['redis_id'] = 'location'
        kwargs['name'] = kwargs['redis'].hget(
            'bf:Facet:labels',
            'bf:Facet:{0}'.format(kwargs['redis_id']))
        kwargs['items'] = []
        location_keys = kwargs['redis'].zrevrange(
            'bf:Facet:locations:sort',
            0,
            -1,
            withscores=True
            )
        for row in location_keys:
            redis_key = row[0]
            item_name = kwargs['redis'].hget('bf:Facet:labels',
                                             redis_key)
            kwargs['items'].append(
                FacetItem(count=int(row[1]),
                    key=redis_key,
                    name=item_name,
                    redis=kwargs['redis']))
        super(LocationFacet, self).__init__(**kwargs)

class PublicationYearFacet(Facet):

    def __init__(self, **kwargs):
        kwargs['redis_id'] = 'pub-year'
        kwargs['name'] = kwargs['redis'].hget(
            'bf:Facet:labels',
            'bf:Facet:{0}'.format(kwargs['redis_id']))
        kwargs['items'] = []
        pub_year_keys = kwargs['redis'].zrevrange(
            'bf:Facet:pub-year:sort',
            0,
            -1,
            withscores=True)
        for row in pub_year_keys:
            redis_key = row[0]
            item_name = kwargs['redis'].hget('bf:Facet:labels',
                                             redis_key)
            kwargs['items'].append(
                FacetItem(count=int(row[1]),
                    key=redis_key,
                    name=item_name,
                    redis=kwargs['redis']))
        super(PublicationYearFacet, self).__init__(**kwargs)
                                             
        


class BIBFRAMESearch(object):

    def __init__(self,**kwargs):
        self.query = kwargs.get('q')
        self.type_of = kwargs.get('type_of', 'kw')
        self.redis_datastore = kwargs.get('redis_datastore',
                                          REDIS_DATASTORE)
        search_key = kwargs.get('search_key', None)
        self.offset = kwargs.get('offset', OFFSET)
        if search_key is not None:
            # Checks to see if history key exists in datastore
            if not self.redis_datastore.exists(search_key):
                # Search key has expired set to None to create a new search
                # key
                search_key = None
            else:
                self.search_key = search_key
                # Reset search key expiration to 15 minutes
                self.redis_datastore.expire(self.search_key, 900)
        if search_key is None:
            self.search_key = 'rlsp-query:{0}'.format(
                                   self.redis_datastore.incr('global rlsp-query'))
            
            shard_incr = self.redis_datastore.incr(
                'global {0}:shard'.format(self.search_key))
            self.active_shard = "{0}:shard:{1}".format(
                self.search_key,
                shard_incr)
            self.redis_datastore.zadd(self.search_key,
                                      float(shard_incr),
                                      self.active_shard)
        self.facets, self.fails  = [], []

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
                "query-key":self.search_key,
                'works': []}
        if with_results is True:
            for shard_key in self.redis_datastore.zrange(self.search_key,
                                                         0,
                                                         -1):
                for instance_key in self.redis_datastore.smembers(
                    shard_key):
                    work_key = self.redis_datastore.hget(instance_key,
                                                         'instanceOf')
                    creator_keys = []
                    if self.redis_datastore.exists("{0}:rda:isCreatedBy".format(
                        work_key)):
                        creator_keys = list(
                            self.redis_datastore.smembers(
                                "{0}:rda:isCreatedBy".format(work_key)))
                    else:
                        creator_key = self.redis_datastore.hget(
                            work_key,
                            'rda:isCreatedBy')
                        if creator_key is not None:
                            creator_keys.append(creator_key)
                    creators = []
                    for key in creator_keys:
                        creator_name = self.redis_datastore.hget(
                            key,
                            'rda:preferredNameForThePerson')
                        if key.count('Person') > -1:
                            creator_url = '/apps/discovery/Person/{0}'
                        elif key.count('Organization') > -1:
                            creator_url = '/apps/discovery/Organization/{0}'
                        else:
                            creator_url = '/apps/discovery/{0}'
                        creator_url = creator_url.format(key.split(":")[-1])  
                        creators.append({'CreatorName': unicode(creator_name,
                                                                errors='ignore'),
                                         'CreatorURL': unicode(creator_url,
                                                               errors='ignore')})
    
                    work_parts = work_key.split(":")
                    title_key = self.redis_datastore.hget(work_key,
                                                          'title')
                    raw_title = self.redis_datastore.hget(title_key,
                                                          'label')
                    found_text = u"<span style='background-color: yellow'>{0}</span>".format(self.query)
    
                    title = raw_title.decode('utf-8',
                                             errors='replace')
                    title = title.replace(self.query, found_text)
                    
                    work = {'CoverArt': '/static/img/publishing_48x48.png',
                            'WorkCreators': creators,
                            'WorkTitle': title, 
                            'WorkURL': '/apps/discovery/{0}/{1}'.format(
                                work_parts[-2],
                                work_parts[-1]),
                            }
                    info['works'].append(work)
        else:
            info['works'] = self.redis_datastore.zcard(self.search_key)
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
        # Resets active shard
        self.active_shard = self.redis_datastore.zrange(
            self.search_key,
            0,
            0)[0]
        self.generate_facets()
        self.redis_datastore.zadd('bibframe-searches', 
                                 time.time(),
                                 self.__json__(with_results=False))
        # Should set query and all shard keys to expire in 15 minutes
        for shard_key in self.redis_datastore.zrange(
            self.search_key,
            0,
            -1):
            self.redis_datastore.expire(shard_key, 900)
        self.redis_datastore.expire(self.search_key, 900)


    def __add_to_query__(self, work_key):
        "Adds all found bf:Instances to search"
        # First check to see if active shard is less than global
        # offset
        if self.redis_datastore.scard(self.active_shard) > self.offset:
            redis_incr = self.redis_datastore.incr(
                'global {0}:shard'.format(self.search_key))
            self.active_shard = "{0}:shard:{1}".format(
                self.search_key,
                redis_incr)
            self.redis_datastore.zadd(self.search_key,
                                      float(redis_incr),
                                      self.active_shard)
        instance_key = self.redis_datastore.hget(work_key,
                                                 'hasInstance')
        if instance_key is None:
            work_instances = self.redis_datastore.smembers(
                     '{0}:hasInstance'.format(work_key))
            for instance_key in list(work_instances):
                self.redis_datastore.sadd(self.active_shard,
                                          instance_key)
        else:
            self.redis_datastore.sadd(self.active_shard,
                                      instance_key)

    def author(self):
        found_creators = person_authority_app.person_search(self.query,
			                                    redis_datastore=self.redis_datastore)
        for work_key in found_creators:
            self.__add_to_query__(work_key)


    def creative_works(self, shard=0):
        works, work_class = [], bibframe.models.Work
        shard_key = self.redis_datastore.zrange(self.search_key,
                                                shard,
                                                shard)[0]
        for entity_key in self.redis_datastore.smembers(shard_key):
            
            work_key = None
            # If entity is bf:Instance, get entity's Creative Work
            if entity_key.startswith('bf:Instance'):
                work_key = self.redis_datastore.hget(entity_key,
                                                     'instanceOf')
            else:
                work_key = entity_key
            # Checks to see if entity_key is a Creative Work or child 
            for work in bibframe.models.CREATIVE_WORK_CLASSES:
                prefix = "bf:{0}".format(work)
                if work_key.startswith(prefix):
                    work_class = getattr(bibframe.models,
                                         work)
            if work_key is not None:
                works.append(work_class(redis_key=work_key,
                                        redis_datastore=self.redis_datastore))
        return works
        

    def __generate_facet__(self, name, sort_key):
        facet = Facet(name=name,
                      redis=self.redis_datastore)
        for facet_key in self.redis_datastore.zrevrange(sort_key,
                                                      0,
                                                      -1):
            entity_keys = self.redis_datastore.sinter(facet_key, 
                                                      self.active_shard)
            entity_count = len(entity_keys)
            if entity_count > 0:
                facet_item = FacetItem(name=facet_key.split(":")[-1],
                                       key=facet_key,
                                       redis=self.redis_datastore)
                facet.items.append(facet_item)
        return facet
            


    def generate_facets(self):
        facet_keys = ['bf:Facet:format',
                      'bf:Facet:loc-first-letter',
                      'bf:Facet:language',
                      'bf:Facet:PublicationDate']
        self.facets.append(self.__generate_facet__('Formats',
                                                   'bf:Annotation:Facet:Formats'))
        self.facets.append(self.__generate_facet__('Languages',
                                                   'bf:Annotation:Facet:Languages'))
##        lib_location = {'name': 'Libraries',
##                        'items': [],
##                        'count': 0}
##        for lib_key in  self.redis_datastore.hvals('prospector-institution-codes'):
##            lib_owner_key = "{0}:resourceRole:own".format(lib_key)
##            instance_keys = self.redis_datastore.smembers(lib_owner_key)
##            search_set = self.redis_datastore.smembers(self.search_key)
##            lib_results = instance_keys.intersection(search_set)
##            if len(lib_results) > 0:
##                lib_location['items'].append({'name': self.redis_datastore.hget(lib_key, 
##                                                                             'label'),
##                                              'count': len(lib_results)})
##            lib_location['count'] += len(lib_results)
##        lib_location['items'].sort(key=lambda x: x.get('count', 0))
##        lib_location['items'].reverse()
##        self.facets.append(lib_location)
                

    def journal_title(self):
        self.title()
        self.redis_datastore.sinterstore(self.search_key, 
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
            self.redis_datastore.sadd(self.search_key, key)



    def number_lccn(self):
        instance_key = self.redis_datastore.hget('lccn-hash', self.query.strip())
        if instance_key is not None:
            self.redis_datastore.sadd(self.search_key, instance_key)
        

    def number_med(self):
        instance_key = self.redis_datastore.hget('nlm-hash', self.query.strip())
        if instance_key is not None:
            self.redis_datastore.sadd(self.search_key, instance_key)
      

    def number_oclc(self):
        pass

    def subject_children(self):
        pass

    def subject_lc(self):
        pass

    def title(self):
        # Search using Title App
        found_titles = title_app.search_title(self.query,
                                              self.redis_datastore)
        for title_key in found_titles:
            self.__add_to_query__(title_key)


def get_news():
    news = []
    # In demo mode, just create a news item regarding the
    # statistics of the REDIS_DATASTORE
    if REDIS_DATASTORE is not None:
        body_text = "<p><strong>Totals:</strong>"
        for key in CREATIVE_WORK_CLASSES:
            body_text += '{0} = {1}<br>'.format(
                key,
                REDIS_DATASTORE.get('global bf:{0}'.format(key)))
        body_text += '</p><p>Total number of keys={0}</p>'.format(
            REDIS_DATASTORE.dbsize())
        item = {'heading': 'Current Statistics for Redis Datastore',
                'body': body_text}
        news.append(item)
##        body_html = '<ul>'
##        for row in  REDIS_DATASTORE.zrevrange('prospector-holdings',
##                                               0,
##                                               -1,
##                                              withscores=True):
##            org_key, score = row[0], row[1]
##            body_html += '''<li>{0} Total Holdings={1}</li>'''.format(
##                             REDIS_DATASTORE.hget(org_key, 'label'),
##                             score)
##        body_html += '</ul>'
##        item2 = {'heading': 'Institutional Collections',
##                 'body': body_html}
##        news.append(item2)
    return news
        

def get_facets(redis_datastore):
    """
    Helper Function returns a list of Facets

    :param annotation_ds: Annotation Datastore
    """
    facets = []
    facets.append(AccessFacet(redis=redis_datastore))
    facets.append(FormatFacet(redis=redis_datastore))
    facets.append(LanguageFacet(redis=redis_datastore))
    facets.append(LocationFacet(redis=redis_datastore))
    facets.append(LCFirstLetterFacet(redis=redis_datastore))
    facets.append(PublicationYearFacet(redis=redis_datastore))

    return facets



def get_result_facets(work_keys):
    """
    Helper function takes a list of Creative Works keys and returns
    all of the facets associated with those entities.

    :param work_keys: Work keys
    """
    facets = []
    return facets

    



