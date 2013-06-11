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

CREATIVE_WORK_REDIS = settings.CREATIVE_WORK_REDIS
INSTANCE_REDIS = settings.INSTANCE_REDIS
AUTHORITY_REDIS = settings.AUTHORITY_REDIS
ANNOTATION_REDIS = settings.ANNOTATION_REDIS
OPERATIONAL_REDIS = settings.OPERATIONAL_REDIS

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
        if rdf_classes[class_name]['parent'] is not None:
            parent_class = getattr(sys.modules[__name__],
                                   rdf_classes[class_name]['parent'])
                                   
        new_class = type(class_name,
                         (parent_class,),
                         rdf_classes[class_name].get('attributes'))
        setattr(sys.modules[__name__],
                class_name,
                new_class)
        
        
        
    
    


#
def old_load_rdf():
    """
    Helper function loads all rdf files in the Fixures directory, creating
    attributes that are associated with each class
    """
    range_xpath = "{{{1}}}Class/{{{1}}}range/{{{0}}}Description".format(
        RDF,
        RDFS)
    bibframe_rdf_dir = os.path.join(settings.PROJECT_HOME,
                                    "bibframe",
                                    "fixures")
    bibframe_files = next(os.walk(bibframe_rdf_dir))[2]
    for filename in bibframe_files:
        class_name, ext = os.path.splitext(filename)
        if ext == '.rdf':
            rdf_xml = etree.parse(os.path.join(bibframe_rdf_dir,
                                               filename))
            all_ranges = rdf_xml.findall(range_xpath)
            params = {'name': class_name}
            marc_mapping = {}
            for desc in all_ranges:
                attribute = os.path.split(
                    desc.attrib.get("{{{0}}}about".format(RDF)))[1]
                params[attribute] = None
                label = desc.find("{{{0}}}label".format(RDFS))
                if label is not None:
                    OPERATIONAL_REDIS.hsetnx(
                        'bf:vocab:{0}:labels'.format(class_name),
                        attribute,
                        label.text)
                marc_fields = desc.findall(
                    '{{{0}}}marcField'.format(BF_ABSTRACT))
                for field in marc_fields:
                    if marc_mapping.has_key(attribute):
                        marc_mapping[attribute].append(field.text)
                    else:
                        marc_mapping[attribute] = [field.text,]
                params['marc_map'] = marc_mapping
                                           
            new_class = type(class_name,
                             (RedisBibframeInterface,),
                             params)
            setattr(sys.modules[__name__],
                    class_name,
                    new_class)

def update_rdf():
    "Helper function downloads the latest RDF documents from bibframe"
    bf_base_url = 'http://bibframe.org/vocab/{0}.rdf'
    for name in ACTIVE_ENTITIES:
        bf_url = bf_base_url.format(name)
        bf_rdf = urllib2.urlopen(bf_url).read()
        rdf_file = open(os.path.join(settings.PROJECT_HOME,
                                     "bibframe",
                                     "fixures",
                                     "{0}.rdf".format(name)),
                        "wb")
        rdf_file.write(bf_rdf)
        rdf_file.close()
        print("Updated RDF for {0}".format(name))
                   

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
              redis_object):
    """
    Save keys 

    Parameters:
    entity_key -- Entity Key
    name -- Name of entity
    value -- Value of entity
    redis_object -- Redis Datastore
    """
    new_redis_key = "{0}:{1}".format(entity_key, name)
    all_keys_key = "{0}:keys".format(entity_key)
    redis_object.sadd(all_keys_key, new_redis_key)
    if value is None:
        redis_object.srem(all_keys_key,
                          new_redis_key)
    elif type(value) is list:
        redis_object.lpush(new_redis_key, value)
    elif type(value) is set:
        if len(value) == 1:
            redis_object.hset(entity_key,
                              name,
                              list(value)[0])
            redis_object.srem(all_keys_key,
                              new_redis_key)
        else:
            for member in list(value):
                redis_object.sadd(new_redis_key,
                                  member)
    elif type(value) is dict:
        for new_key, new_value in value.iteritems():
            redis_object.hset(new_redis_key,
                              new_key,
                              new_value)
    else:
        redis_object.hset(entity_key,
                          name,
                          value)
        # Remove new_redis_key from all_keys_key as new_redis_key
        # is not a distinct Redis key
        redis_object.srem(all_keys_key,
                          new_redis_key)

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
            count = self.redis_datastore.incr("global bf:{0}".format(self.name))
            self.redis_key = "bf:{0}:{1}".format(self.name,
                                                 count)
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
                if prop.startswith("__"):
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
