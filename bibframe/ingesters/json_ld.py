"""JSON Linked Data Module for Ingestion of json linked data files into
the Redis Library Services Platform

"""
__author__ = "Jeremy Nelson"

import datetime
import json
import os
import sys
import urllib
import urllib2

from aristotle.settings import REDIS_DATASTORE
from bibframe.ingesters.Ingester import Ingester
from organization_authority.redis_helpers import get_or_add_organization
from title_search.redis_helpers import index_title, search_title
import bibframe.models as models
from lxml import etree
from rdflib import RDF, RDFS, Namespace


class JSONLinkedDataIngester(Ingester):
    "Class takes JSON Linked Data and ingests into RLSP"

    def __init__(self, **kwargs):
        "Creates an instance of the class"
        super(JSONLinkedDataIngester, self).__init__(**kwargs)
        self.linked_data = None

    def __extract_authority_lcsh__(self, authority_uri):
        """Helper function returns bf:Authority key based on lcsh names
        uri

        Parameters:
        authority_uri -- LCSH authority URI
        """
        authority_key = self.redis_datastore.hget(
            'lcna-hash',
            authority_uri)
        if authority_key is None:
            authority_json = json.load(
                urllib2.urlopen('{0}.json'.format(authority_uri)))
            authority_label = authority_json.get(
                u"<{0}>".format(authority_uri)).get(
                    u'<http://www.w3.org/2004/02/skos/core#prefLabel>')
            if authority_label is not None:
                info = {'label': authority_label[0].get('value'),
                        'lcna-uri': authority_uri}
                new_organization = get_or_add_organization(
                    info,
                    self.redis_datastore)
                new_organization.save()
                self.redis_datastore.hset(
                    'lcna-hash',
                    authority_uri,
                    new_organization.redis_key)
                authority_key = new_organization.redis_key
        return authority_key
           

    def __extract_title_entity__(self, title_info):
        """Helper function gets existing bf:TitleEntity or creates a
        new bf:TitleEntity, returns bf:TitleEntity redis key

        Parameters:
        title_info -- JSON dict of title information
        """
        new_title = models.TitleEntity(redis_datastore=self.redis_datastore)
        new_title.titleValue = title_info.get('bf:titleValue')
        new_title.label = new_title.titleValue
        new_title.save()
        return new_title.redis_key
                                       
        

    def __extract_instances__(self, instances):
        """Helper function returns a list of bf:Instance redis keys 

        Parameters:
        topics -- List of dicts with topic info
        """
        instance_keys = []
        for instance in instances:
            bf_instance = models.Instance(redis_datastore=self.redis_datastore)
            for key, value in instance.iteritems():
                if key.startswith('bf:'):
                    key = key[3:]
                if key.startswith('@'):
                    continue
                setattr(bf_instance, key, value)
            bf_instance.save()
            instance_keys.append(bf_instance.redis_key)
        return instance_keys
            
            

    def __extract_topics__(self, topics):
        """Helper function returns a list of bf:Topic redis keys 

        Parameters:
        topics -- List of dicts with topic info
        """
        topic_keys = []
        for topic in topics:
            topic_id = topic.get('bf:identifier')
            topic_key = self.redis_datastore.hget(
                'lcsh-hash',
                topic_id)
            if topic_key is not None:
                topic_keys.append(topic_key)
            else:
                bf_topic = models.Topic(
                    redis_datastore=self.redis_datastore,
                    label=topic.pop('bf:label'))
                for key, value in topic.iteritems():
                    if key == 'bf:hasAuthority':
                        value = self.__extract_authority_lcsh__(value)
                    if key.startswith('@'):
                        continue
                    # Removes bf prefix
                    if key.startswith('bf:'):
                        key = key[3:]
                    setattr(bf_topic, key, value)
                bf_topic.save()
                topic_keys.append(bf_topic.redis_key)
                self.redis_datastore.hset(
                    'lcsh-hash',
                    topic_id,
                    bf_topic.redis_key)
        return topic_keys

    def __ingest__(self):
        "Helper function extracts info from JSON and ingests into RLSP"
        if self.linked_data is None:
            return
        if self.linked_data.has_key('@context'):
            self.linked_data.pop('@context')
        work = dict()
        # Assumes type is a bf Creative Work class or subclass
        work_name = self.linked_data.get('@type')[3:]
        if not self.linked_data.get('@type').startswith('bf:') or\
           hasattr(models, work_name) is False:
            raise ValueError("Linked Data is not in the bibframe namespace")
        work_class = getattr(models, work_name)
        new_work = work_class(redis_datastore=self.redis_datastore)
        new_work.subject = self.__extract_topics__(
            self.linked_data.pop('bf:subject'))
        new_work.subject = set(new_work.subject)
        work['title'] = self.__extract_title_entity__(
            self.linked_data.pop('bf:title'))
        new_work.title = work['title']
        work['hasInstance'] = self.__extract_instances__(
            self.linked_data.pop('bf:hasInstance'))
        new_work.hasInstance = work['hasInstance']
        for key, value in self.linked_data.iteritems():
            if key.startswith('@'):
                continue
            if key.startswith("bf:"):
                key = key[3:]
            if type(value) == list:
                value = set(value)
            setattr(new_work, key, value)
        new_work.save()
        for instance_key in work['hasInstance']:
            self.redis_datastore.hset(instance_key,
                                      'instanceOf',
                                      new_work.redis_key)
            
            

        
        
        

        
        
        

        
        
        











