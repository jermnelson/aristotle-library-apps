"""
 :mod:models` - BIBFRAME models based upon rdf representations
 of http://bibframe.org's Resource, Creative Work, Instance, Annotation,
 and Authority classes.
"""
__author__ = "Jeremy Nelson"

import redis,datetime,json,urllib2
import os,sys, inspect
from lxml import etree
from rdflib import RDF,RDFS
from django.db import models
try:
    import aristotle.settings as settings
    CREATIVE_WORK_REDIS = settings.CREATIVE_WORK_REDIS
    INSTANCE_REDIS = settings.INSTANCE_REDIS
    AUTHORITY_REDIS = settings.AUTHORITY_REDIS
    ANNOTATION_REDIS = settings.ANNOTATION_REDIS
    OPERATIONAL_REDIS = settings.OPERATIONAL_REDIS
except ImportError, e:
    redis_host = '0.0.0.0'
    CREATIVE_WORK_REDIS = redis.StrictRedis(port=6380)
    INSTANCE_REDIS = redis.StrictRedis(port=6381)
    AUTHORITY_REDIS = redis.StrictRedis(port=6382)
    ANNOTATION_REDIS = redis.StrictRedis(port=6383)
    OPERATIONAL_REDIS = redis.StrictRedis(port=6379)


#
def load_rdf():
    """
    Helper function loads all rdf files in the Fixures directory, creating
    attributes that are associated with each class
    """
    range_xpath = "{{{0}}}Description/{{{1}}}range/{{{0}}}Description".format(RDF,RDFS)
    bibframe_rdf_dir = os.path.join(settings.PROJECT_HOME,"bibframe","fixures")
    bibframe_files = next(os.walk(bibframe_rdf_dir))[2]
    for filename in bibframe_files:
        class_name,ext = os.path.splitext(filename)
        if ext == '.rdf':
            rdf_xml = etree.parse(os.path.join(bibframe_rdf_dir,filename))
            all_ranges = rdf_xml.findall(range_xpath)
            params = {'name':class_name}
            for desc in all_ranges:
                attribute = os.path.split(desc.attrib.get("{{{0}}}about".format(RDF)))[1]
                params[attribute] = None
                label = desc.find("{{{0}}}label".format(RDFS))
                if label is not None:
                    OPERATIONAL_REDIS.hsetnx('bibframe:vocab:{0}:labels'.format(class_name),
                                             attribute,
                                             label.text)
            new_class = type(class_name,
                             (RedisBibframeInterface,),
                             params)
            setattr(sys.modules[__name__],class_name,new_class)

def process_key(bibframe_key,
                redis_instance):
    """
    Helper function 

    :param bibframe_key: Redis bibframe entities key
    :param redis_instance: Redis instance to check 
    """
    output = {}
    if not redis_instance.exists(bibframe_key):
        raise ValueError("Redis-key of {0} doesn't exist in datastore".format(bibframe_key))
    for key,value in redis_instance.hgetall(bibframe_key).iteritems():
        output[key] = value
    if redis_instance.exists("{0}:keys".format(bibframe_key)):
        for key in list(redis_instance.smembers("{0}:keys".format(bibframe_key))):
            attribute_name = key.split(":")[-1]
            key_type = redis_instance.type(key) 
            if key_type == 'hash':
                output[attribute_name] = {}
                hash_values = redis_instance.hgetall(key)
                for k,v in hash_values.iteritems():
                    output[attribute_name][k] = v
            elif key_type == 'set':
                output[attribute_name] = redis_instance.smembers(key)
            elif key_type == 'list':
                output[attribute_name] = redis_instance.lrange(key,0,-1)
    return output

def save_keys(entity_key,name,value,redis_object):
    """
    Save keys 

    """
    new_redis_key = "{0}:{1}".format(entity_key,name)
    all_keys_key = "{0}:keys".format(entity_key)
    redis_object.sadd(all_keys_key,new_redis_key)
    if value is None:
        redis_object.srem(all_keys_key,new_redis_key)
    elif type(value) is list:
        redis_object.lpush(new_redis_key, value)
    elif type(value) is set:
        if len(value) == 1:
            redis_object.hset(entity_key,name,list(value)[0])
            redis_object.srem(all_keys_key,new_redis_key)
        else:
            for member in list(value):
                redis_object.sadd(new_redis_key,member)
    elif type(value) is dict:
        redis_object.sadd(all_keys_key,new_redis_key)
        for nk, nv in value.iteritems():
            redis_object.hset(new_redis_key,
                              nk,
                              nv)
    else:
        redis_object.hset(entity_key,name,value)
        # Remove new_redis_key from all_keys_key as new_redis_key
        # is not a distinct Redis key
        redis_object.srem(all_keys_key,new_redis_key)

          

class RedisBibframeInterface(object):
    """
    Parent class for all classes of the Bibliographic Framework's
    based upon RDF.
    """
    

    def __init__(self,
                 primary_redis=None,
                 redis_key=None,
                 **kwargs):
        """
        Initializes a RedisBibframeInterface class provides Redis support for a 
        BIBFRAME class. 

        :param primary_redis: Redis instance used for primary 
        """
        self.primary_redis = primary_redis
        self.redis_key = redis_key
        self.__load__(kwargs)
        
    
    def __load__(self,kwargs):
        """
    Internal method either sets instance's properties or sets new
    attribute values from passed kwargs in __init__ or upon a
    refresh from the Redis server.
        """
        if self.redis_key is not None:
            kwargs.update(process_key(self.redis_key,
                                      self.primary_redis))
        for key,value in kwargs.iteritems():
            setattr(self,key,value)

    def feature(self,
                name=None):
        """
        Method returns a feature of the class.

        :param name: Name of feature
        """
        if hasattr(self,name):
            if name.startswith("redis") or name.startswith("__"):
                return None
            else:
                return getattr(self,name)
        # Returns a dict of all features for the class
        output = {}
        if name is None:
            for row in dir(self):
                if row.startswith("redis") or row.startswith("__"):
                    continue
                else:
                    output[row] = getattr(self,row)
        return output
   

    def save(self,
             property_name=None):
        """
        Method saves the class attributes and properties to the 
        class's primary redis or creates a new root Redis key 
        and supporting keys to the primary redis datastore.
        """
        if self.primary_redis is None:
            raise ValueError("Cannot save, no primary_redis")
        if self.redis_key is None:
            self.redis_key = "bibframe:{0}:{1}".format(self.name,
                                                       self.primary_redis.incr("global bibframe:{0}".format(self.name)))
            self.primary_redis.hset(self.redis_key,
                                    'created_on',
                                    datetime.datetime.utcnow().isoformat())
        else:
            if not self.primary_redis.exists(self.redis_key):
                raise ValueError("Cannot save, {0} doesn't exist in primary_redis port={1}".format(self.redis_key,
                                                                                              self.primary_redis.info()['tcp-port']))
        # If property_name is None, save everything
        if property_name is None:
            all_properties = dir(self)
            
            redis_pipeline = self.primary_redis.pipeline()
       
            for property in all_properties:
                if property.startswith("__"):
                    continue
                elif property == 'primary_redis' or property == 'redis_key' or property == 'name':
                    continue
                elif inspect.ismethod(getattr(self,property)):
                    continue
                else:
                    prop_value = getattr(self,property)
                    save_keys(self.redis_key,property,prop_value,redis_pipeline)
                    redis_pipeline.execute()
        # Specific redis key structure to save instead of entire object, checks
        # both the instance and the instance's attributes dictionary
        else:
            if hasattr(self,property_name): 
                prop_value = getattr(self,property_name)
            else:
                err_msg = '''Cannot save {0}, 
                Redis Key of {1} does not have {2}'''.format(self.attributes.name,
                                                             self.redis_key,
                                                             property_name)
                raise ValueError(err_msg)
            save_keys(self.redis_key, 
                      property_name, 
                      prop_value, 
                      self.primary_redis)
       

load_rdf() 
