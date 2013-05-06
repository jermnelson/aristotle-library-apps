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
                    OPERATIONAL_REDIS.hsetnx('bf:vocab:{0}:labels'.format(class_name),
                                             attribute,
                                             label.text)
            new_class = type(class_name,
                             (RedisBibframeInterface,),
                             params)
            setattr(sys.modules[__name__],class_name,new_class)

def process_key(bibframe_key,
                client=None,
                redis_instance=None):
    """Helper function returns a info dict about a bibframe entity 

    Function extracts information from either a RedisShard or Redis
    instance and returns a dictionary of information
    
     
    Parameters:
    bibframe_key -- Redis bibframe entities key
    client == RedisShard to check, defaults to None
    redis_instance -- Redis instance to check, defaults to None 
    """
    output = {}
    if client is None and redis_instance is None:
        msg = "process_key requires client or redis_instance"
        raise RedisBibframeModelError(msg)
    if client is not None and client.exists(bibframe_key) is None:
        msg = "{0} doesn't exist in client"
        raise RedisBibframeModelError(msg)
    if redis_instance is not None and\
       redis_instance.exists(bibframe_key) is None:
        msg = "{0} doesn't exist in redis_instance".format(bibframe_key)
        raise RedisBibframeModelError(msg)
    if client is not None:
        redis_server = client
    else:
        redis_server = redis_instance
    for key, value in redis_server.hgetall(bibframe_key).iteritems():
        output[key] = value
    if redis_server.exists("{0}:keys".format(bibframe_key)):
        for key in list(redis_server.smembers("{0}:keys".format(bibframe_key))):
            attribute_name = key.split(":")[-1]
            key_type = redis_server.type(key) 
            if key_type == 'hash':
                output[attribute_name] = {}
                hash_values = redis_server.hgetall(key)
                for k,v in hash_values.iteritems():
                    output[attribute_name][k] = v
            elif key_type == 'set':
                output[attribute_name] = redis_server.smembers(key)
            elif key_type == 'list':
                output[attribute_name] = redis_server.lrange(key,0,-1)
    return output

def save_keys(entity_key,name,value,redis_object):
    """
    Save keys 

    """
    new_redis_key = "{0}:{1}".format(entity_key,name)
    all_keys_key = "{0}:keys".format(entity_key)
    redis_object.sadd(all_keys_key, new_redis_key)
    if value is None:
        redis_object.srem(all_keys_key,new_redis_key)
    elif type(value) is list:
        redis_object.lpush(new_redis_key, value)
    elif type(value) is set:
        if len(value) == 1:
            redis_object.hset(entity_key, name, list(value)[0])
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

class RedisBibframeModelError(Exception):
    """Redis Bibframe Model Error
     
    Error raised when a Model Error occurs
    """
    def __init__(self, message):
        self.value = message

    def __str__(self):
        return repr(self.value)

class RedisBibframeInterface(object):
    """
    Parent class for all classes of the Bibliographic Framework's
    based upon RDF.
    """
    

    def __init__(self,
                 client=None,
                 primary_redis=None,
                 redis_key=None,
                 **kwargs):
        """
        Initializes a RedisBibframeInterface class provides Redis support for a 
        BIBFRAME class. 

        :param primary_redis: Redis instance used for primary 
        """
        self.client = client
        self.primary_redis = primary_redis
        self.redis_key = redis_key
        self.__load__(kwargs)
        
    
    def __load__(self, kwargs):
        """
        Internal method either sets instance's properties or sets new
        attribute values from passed kwargs in __init__ or upon a
        refresh from the Redis server.
        """
        if self.redis_key is not None:
            kwargs.update(process_key(self.redis_key,
                                      self.primary_redis))
        for key, value in kwargs.iteritems():
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
        if self.client is None and self.primary_redis is None:
            msg = "Cannot save missing RedisShard client or Primary Redis"
            raise RedisBibframeModelError(msg)
        if self.redis_key is None:
            redis_base = "bf:{0}".format(self.name)
            created_on = datetime.datetime.utcnow().isoformat()
            if self.client is not None:
                redis_id = self.client.incr('global {0}'.format(redis_base))
            else:
                redis_id = self.primary_redis.incr('global {0}'.format(redis_base))
            self.redis_key = "{0}:{1}".format(redis_base, redis_id)
            if self.client is not None:
                self.client.hset(self.redis_key, created_on)
            else:
                self.primary_redis.hset(self.redis_key, created_on)
        else:
            if self.client is not None:
                if not self.client.exists(self.redis_key):
                    error_msg = "Save failed {0}, no existance in client".format(
                                    self.redis_key)
                    raise RedisBibframeModelError(error_msg)
            else:
                if not self.primary_redis.exists(self.redis_key):
                    error_msg = "Save failed for {0} in primary redis".format(
                                    self.redis_key)
                    raise RedisBibframeModelError(error_msg)
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
                    prop_value = getattr(self, property)
                    save_keys(self.redis_key,property,
                              prop_value,
                              redis_pipeline)
                    redis_pipeline.execute()
        # Specific redis key structure to save instead of entire object, checks
        # both the instance and the instance's attributes dictionary
        else:
            if hasattr(self,property_name): 
                prop_value = getattr(self, property_name)
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
