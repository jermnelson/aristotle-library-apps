"""
 :mod:models` - BIBFRAME models based upon rdf representations
 of http://bibframe.org's Resource, Creative Work, Instance, Annotation,
 and Authority classes.
"""
__author__ = "Jeremy Nelson"

import datetime
import inspect
import os
import sys
import urllib2

from lxml import etree
from rdflib import RDF, RDFS, Namespace

BF_ABSTRACT = Namespace('http://bibframe.org/model-abstract/')

import aristotle.settings as settings
from aristotle.settings import REDIS_DATASTORE


ACTIVE_ENTITIES = ['Agent',
                   'Annotation',
                   'Article',
                   'Audio',
                   'Authority',
                   'Book',
                   'ClassificationEntity',
                   'CoverArt',
                   'Dataset',
                   'Dissertation',
                   'Family',
                   'Globe',
                   'Holding',
                   'Instance',
                   'Jurisdiction',
                   'Legislation',
                   'Manuscript',
                   'Map',
                   'Meeting',
                   'MixedMaterial',
                   'MovingImage',
                   'NonmusicalAudio',
                   'NotatedMovement',
                   'NotatedMusic',
                   'Organization',
                   'Person',
                   'Place',
                   'RemoteSensingImage',
                   'Review',
                   'Serial',
                   'SoftwareOrMultimedia',
                   'StillImage',
                   'Tactile',
                   'TemporalConcept',
                   'ThreeDimensionalObject',
                   'TitleEntity',
                   'TopicalConcept',
                   'Work']

CREATIVE_WORK_CLASSES = ['Article',
                         'Book',
                         'Dissertation',
                         'Manuscript',
                         'Map',
                         'MixedMaterial',
                         'MovingImage',
                         'NotatedMusic',
                         'MusicalAudio',
                         'NonmusicalAudio',
                         'Serial',
                         'SoftwareOrMultimedia']

def load_rdf():
    "Helper function creates BIBFRAME classes from vocab.rdf"
    vocab_rdf = etree.parse(os.path.join(settings.PROJECT_HOME,
                                         'bibframe',
                                         'fixures',
                                         'vocab.rdf'))
    rdf_classes = {}
    rdf_class_order = []
    rdfs_class_elems = vocab_rdf.findall('{{{0}}}Class'.format(RDFS))
    for row in rdfs_class_elems:
        class_name = os.path.split(
            row.attrib.get('{{{0}}}about'.format(RDF)))[-1]
        rdf_class_order.append(class_name)
        parent_class = row.find("{{{0}}}subClassOf".format(RDFS))
        if parent_class is not None:
            parent_url = parent_class.attrib.get('{{{0}}}resource'.format(RDF))
            parent_name = os.path.split(parent_url)[-1]
            if rdf_classes.has_key(parent_name):
                rdf_classes[parent_name]['children'].append(class_name)
            else:
                rdf_classes[parent_name] = {'children': [class_name,],
                                            'attributes': {},
                                            'parent': None}
        else:
            parent_name = None
        if not rdf_classes.has_key(class_name):
            rdf_classes[class_name] = {'attributes': {'name': class_name},
                                       'children': [],
                                       'parent': parent_name}
    rdfs_resources_elems = vocab_rdf.findall("{{{0}}}Resource".format(RDFS))
    for row in rdfs_resources_elems:
        attribute_uri = row.attrib.get('{{{0}}}about'.format(RDF))
        attrib_name = os.path.split(attribute_uri)[-1]
        if not REDIS_DATASTORE.hexists('bf:vocab:labels',
                                       attrib_name):
            label = row.find('{{{0}}}label'.format(RDFS))
            REDIS_DATASTORE.hset('bf:vocab:labels',
                                 attrib_name,
                                 label.text)
        marc_fields = row.findall('{{{0}}}marcField'.format(BF_ABSTRACT))
        marc_mapping = {}
        for field in marc_fields:
            if marc_mapping.has_key(attrib_name):
                marc_mapping[attrib_name].append(field.text)
            else:
                marc_mapping[attrib_name] = [field.text,]        
        domains = row.findall('{{{0}}}domain'.format(RDFS))
        for domain in domains:
            domain_name = os.path.split(
                domain.attrib.get('{{{0}}}resource'.format(RDF)))[-1]
            if rdf_classes.has_key(domain_name) is False:
                raise ValueError("Unknown BIBFRAME class {0}".format(
                    domain_name))
            rdf_classes[domain_name]['attributes'][attrib_name] = None
            if marc_mapping is not None:
                if rdf_classes[domain_name]['attributes'].has_key('marc_map'):
                    rdf_classes[domain_name]['attributes']['marc_map'].update(
                        marc_mapping)
                else:
                    rdf_classes[domain_name]['attributes']['marc_map'] = marc_mapping
                
    # Creates Classes with class hiearchy
    for class_name in rdf_class_order:
        parent_class = RedisBibframeInterface
        # Adds any missing marc mapping in the parent class to the child
        # classes.
        if rdf_classes[class_name]['parent'] is not None:
            parent_name = rdf_classes[class_name]['parent']
            if rdf_classes[
                parent_name]['attributes'].has_key('marc_map'):         
                for parent_map_key, parent_map_rule in rdf_classes[
                    parent_name]['attributes']['marc_map'].iteritems():
                    if rdf_classes[class_name][
                        'attributes'].has_key('marc_map'):
                        if not rdf_classes[class_name][
                            'attributes'][
                                'marc_map'].has_key(parent_map_key):
                            rdf_classes[class_name]['attributes'][
                                'marc_map'][parent_map_key] = parent_map_rule
            parent_class = getattr(sys.modules[__name__],
                                   rdf_classes[class_name]['parent'])
                                   
        new_class = type(class_name,
                         (parent_class,),
                         rdf_classes[class_name].get('attributes'))
        setattr(sys.modules[__name__],
                class_name,
                new_class)
                   

def process_key(bibframe_key,
                redis_instance):
    """
    Helper function 

    :param bibframe_key: Redis bibframe entities key
    :param redis_instance: Redis instance to check 
    """
    output = {}
    if not redis_instance.exists(bibframe_key):
        msg = "Redis-key {0} doesn't exist in datastore".format(bibframe_key)
        raise ValueError(msg)
    for key, value in redis_instance.hgetall(bibframe_key).iteritems():
        output[key] = value
    if redis_instance.exists("{0}:keys".format(bibframe_key)):
        for key in list(
            redis_instance.smembers("{0}:keys".format(bibframe_key))):
            attribute_name = key.split(":")[-1]
            key_type = redis_instance.type(key) 
            if key_type == 'hash':
                output[attribute_name] = {}
                hash_values = redis_instance.hgetall(key)
                for hkey, hvalue in hash_values.iteritems():
                    output[attribute_name][hkey] = hvalue
            elif key_type == 'set':
                output[attribute_name] = redis_instance.smembers(key)
            elif key_type == 'list':
                output[attribute_name] = redis_instance.lrange(key, 0, -1)
    return output

def save_keys(entity_key,
              name,
              value,
              redis_datastore):
    """
    Save keys 

    Parameters:
    entity_key -- Entity Key
    name -- Name of entity
    value -- Value of entity
    redis_datastore -- Redis Datastore
    """
    new_redis_key = "{0}:{1}".format(entity_key, name)
##    all_keys_key = "{0}:keys".format(entity_key)
##    redis_datastore.sadd(all_keys_key, new_redis_key)
    if value is None:
        pass
##        redis_datastore.srem(all_keys_key,
##                             new_redis_key)
    elif type(value) is list:
        if len(value) == 1:
            redis_datastore.hset(entity_key,
                                 name,
                                 value[0])
        else:
            for row in value:
                redis_datastore.lpush(new_redis_key, row)
    elif type(value) is set:
        if len(value) == 1:
            redis_datastore.hset(entity_key,
                              name,
                              list(value)[0])
##            redis_datastore.srem(all_keys_key,
##                              new_redis_key)
        else:
            for member in list(value):
                redis_datastore.sadd(new_redis_key,
                                  member)
    elif type(value) is dict:
        for new_key, new_value in value.iteritems():
            redis_datastore.hset(new_redis_key,
                              new_key,
                              new_value)
    else:
        redis_datastore.hset(entity_key,
                          name,
                          value)
        # Remove new_redis_key from all_keys_key as new_redis_key
        # is not a distinct Redis key
##        redis_datastore.srem(all_keys_key,
##                          new_redis_key)

class RedisBibframeModelError(Exception):
    "Error raised when a Redis BIBFRAME Model Error occurs"
     
    def __init__(self, message):
        "Initializes RedisBibframeModelError"
        super(RedisBibframeModelError, self).__init__()
        self.value = message

    def __str__(self):
        "Method returns string representation of Error"
        return repr(self.value)

class RedisBibframeInterface(object):
    """
    Parent class for all classes of the Bibliographic Framework's
    based upon RDF.
    """
    
    def __init__(self,
                 **kwargs):
        """
        Initializes a RedisBibframeInterface class provides Redis support for a 
        BIBFRAME class. 

        :param redis_datastore: Redis instance used for primary 
        """
        self.redis_datastore, self.redis_key = None, None
        if kwargs.has_key('redis_datastore'):
            self.redis_datastore = kwargs.pop('redis_datastore')
        if kwargs.has_key('redis_key'):
            self.redis_key = kwargs.pop('redis_key')
            self.redis_id = self.redis_key.split(":")[-1]
        self.__load__(**kwargs)
        
    
    def __load__(self, **kwargs):
        """
        Internal method either sets instance's properties or sets new
        attribute values from passed kwargs in __init__ or upon a
        refresh from the Redis server.
        """
        if self.redis_key is not None:
            kwargs.update(process_key(self.redis_key,
                                      self.redis_datastore))
        for key, value in kwargs.iteritems():
            setattr(self,
                    key,
                    value)

    def feature(self,
                name=None):
        """
        Method returns a feature of the class.

        :param name: Name of feature
        """
        if hasattr(self, name):
            if name.startswith("redis") or name.startswith("__"):
                return None
            else:
                return getattr(self, name)
        # Returns a dict of all features for the class
        output = {}
        if name is None:
            for row in dir(self):
                if row.startswith("redis") or row.startswith("__"):
                    continue
                else:
                    output[row] = getattr(self, row)
        return output
   

    def save(self,
             property_name=None):
        """
        Method saves the class attributes and properties to the 
        class's primary redis or creates a new root Redis key 
        and supporting keys to the primary redis datastore.
        """
        if self.redis_datastore is None:
            raise ValueError("Cannot save, no redis_datastore")
        if self.redis_key is None:
            self.redis_id = self.redis_datastore.incr(
                "global bf:{0}".format(self.name))
            self.redis_key = "bf:{0}:{1}".format(self.name,
                                                 self.redis_id)
            self.redis_datastore.hset(self.redis_key,
                                    'created_on',
                                    datetime.datetime.utcnow().isoformat())
        else:
            if not self.redis_datastore.exists(self.redis_key):
                error_msg = """Save failed {0} doesn't exist in
primary redis""".format(self.redis_key)
                raise RedisBibframeModelError(error_msg)
        # If property_name is None, save everything
        if property_name is None:
            all_properties = dir(self)
            #redis_pipeline = self.redis_datastore.pipeline()
            for prop in all_properties:
                if prop.startswith("__") or prop.startswith('marc_map'):
                    continue
                elif prop == 'name' or prop.find('redis') > -1:
                    continue
                elif inspect.ismethod(getattr(self, prop)):
                    continue
                else:
                    prop_value = getattr(self, prop)
                    save_keys(self.redis_key,
                              prop,
                              prop_value,
                              self.redis_datastore)
              #      redis_pipeline.execute()
        # Specific redis key structure to save instead of entire object, checks
        # both the instance and the instance's attributes dictionary
        else:
            if hasattr(self, property_name): 
                prop_value = getattr(self, property_name)
            else:
                err_msg = '''Cannot save, 
                Redis Key of {0} does not have {1}'''.format(
                    self.redis_key,
                    property_name)
                raise ValueError(err_msg)
            save_keys(self.redis_key, 
                      property_name, 
                      prop_value, 
                      self.redis_datastore)

load_rdf()
