"""
 :mod:models` - BIBFRAME models based upon rdf representations
 of http://bibframe.org's Resource, Creative Work, Instance, Annotation,
 and Authority classes.
"""
__author__ = "Jeremy Nelson"

import redis,datetime,json,urllib2
import os,sys
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
	    params = {}
	    for desc in all_ranges:
                attribute = os.path.split(desc.attrib.get("{{{0}}}about".format(RDF)))[1]
		params[attribute] = None
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
    if not redis_instance(bibframe_key):
        raise ValueError("Redis-key of {0} doesn't exist in datastore".format(bibframe_key))
    for key,value in redis_instance.hgetall(bibframe_key).iteritems():
        output[key] = value
    if redis_instance.exists("{0}:keys".format(bibframe_key)):
        for key in list(redis_instance.smembers("{0}:keys".format(bibframe_key))):
            key_type = redis_instance.type(key) 
            if key_type == 'hash':
                output[attrib_key] = {}
		hash_values = redis_instance.hgetall(key)
                for k,v in hash_values.iteritems():
                    output[key][k] = v
            elif key_type == 'set':
                output[key] = redis_instance.smembers(key)
    return output
            


    

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
        self.attributes = {}
        self.primary_redis = primary_redis
	self.redis_key = redis_key
        self.__load__(kwargs)
        
	
    def __load__(self,kwargs):
        """
	    
        """
        if self.redis_key is not None:
            kwargs.extend(process_key(self.redis_key,
                                      self.primary_redis))
	for key,value in kwargs.iteritems():
            if hasattr(self,key):
                setattr(self,key,value)
            else:
                self.attributes[key] = value
               
    def __save__(self,
                 property_name=None):
        """
        Method saves the class attributes and properties to the 
        class's primary redis or creates a new root Redis key 
        and supporting keys to the primary redis datastore.
        """
        if self.primary_redis is None:
            raise ValueError("Cannot save, no primary_redis")
        if self.redis_key is None:
            self.redis_key = self.primary_redis.incr("global bibframe:{0}".format(self.__name__))
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
            
            pipeline = self.primary_redis.pipeline()
            for property in all_properties:
                if property.startswith("__"):
                    continue
                elif property == 'primary_redis' or property == 'redis_key:
                    continue
                elif property == 'attributes':
                    print("{0}".format(property))
            pipeline.execute()
        

  
