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
        Initializes a Resource class properties and support for a BIBFRAME
        class.

        :param primary_redis: Redis instance used for primary 
        """
        self.attributes = {}
        self.primary_redis = primary_redis
	self.redis_key = redis_key
	for key,value in kwargs.iteritems():
            if hasattr(self,key):
                setattr(self,key,value)
            else:
                self.attributes[key] =  value

load_rdf()
