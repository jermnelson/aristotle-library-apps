"""
  :mod:`common` -- Common functions and classes for supporting FRBR Redis datastore
"""
__author__ = 'Jeremy Nelson'

import urllib2,os,logging
import sys,redis
import namespaces as ns
from lxml import etree
try:
    import config
    REDIS_HOST = config.REDIS_HOST
    REDIS_PORT = config.REDIS_PORT
    REDIS_DB = config.REDIS_DB
except ImportError:
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    REDIS_DB = 0

redis_server = redis.StrictRedis(host=REDIS_HOST,
                                 port=REDIS_PORT,
                                 db=REDIS_DB)

def create_key_from_url(raw_url):
    """
    Function parses url, reverses the net location to create a value for use
    as a Redis key.

    :param raw_url: Raw url to extract key, required
    :rtype: String
    """
    org_url = urllib2.urlparse.urlparse(raw_url)
    new_key = ''
    net_location = org_url.netloc
    netloc_list = net_location.split(".")
    netloc_list.reverse()
    for part in netloc_list:
        new_key += '%s.' % part
    new_key = new_key[:-1] # Removes trailing period
    new_key = new_key + org_url.path 
    return new_key

def load_rdf_skos(redis_key,rdf_url):
    """
    Loads skos:ConceptSchema coded in RDF from a URL

    :param redis_key: Base Redis key
    :param rdf_url: URL to RDF document
    """
    raw_rdf = urllib2.urlopen(rdf_url).read()
    skos_rdf = etree.XML(raw_rdf)
    title_element = skos_rdf.find('{%s}ConceptScheme/{%s}title' %\
                                  (ns.SKOS,ns.DC))
    if title_element is None:
        title = redis_key.title()
    else:
        title = title_element.text
    redis_server.set('%s:title' % redis_key,title)
    all_concepts = skos_rdf.findall('{%s}Concept' % ns.SKOS)
    for concept in all_concepts:
        label = concept.find('{%s}prefLabel' % ns.SKOS)
        if label is not None:
            if label.text != 'Published':
                redis_server.sadd(redis_key,
                                  label.text)
                print("Added %s to %s" % (label.text,
                                          redis_key))
    redis_server.save()

def get_python_classname(raw_classname):
    """
    Helper function creates valid Python class name for
    dynamic class creation at runtime.

    :param raw_classname: String from parsed data structure
    :rtype string: Valid Python class name
    """
    class_name = raw_classname.replace(" ","")
    class_name = class_name.replace("-","")
    return class_name

def load_dynamic_classes(rdf_url,redis_prefix,current_module):
    """
    Function takes an URL to an RDF file, parses out and creates
    classes based on the rdfs:Class element.

    :param rdf_url: URL or file location to the RDF file
    :param current_module: Current module
    """
    ns_map = {'rdf':'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
              'rdfs':'http://www.w3.org/2000/01/rdf-schema#',
              'xml':'http://www.w3.org/XML/1998/namespace'}
    try:
        raw_rdf = urllib2.urlopen(rdf_url).read()
    except (urllib2.URLError,ValueError):
        raw_rdf = open(rdf_url,"r").read()
    finally:
        print("Error %s loading %s" % (sys.exc_info(),
                                       rdf_url))
    rdf = etree.XML(raw_rdf)
    all_classes = rdf.findall('{%s}Class' % ns.RDFS)
    for rdf_class in all_classes:
        rdf_ID = rdf_class.get("{%s}ID" % ns.RDF)
        label = rdf_class.find("{%s}label[@{%s}lang='en']" %\
                               (ns.RDFS,
                                ns.XML))
        parent_classes = rdf_class.findall("{%s}subClassOf" %\
                                           ns.RDFS)
        super_classes = []
        for parent in parent_classes:
            parent_id = parent.get("{%s}resource" % ns.RDF)
            parent_id = parent_id.replace("#","")
            parent = rdf.find("{%s}Class[@{%s}ID='%s']" %\
                              (ns.RDFS,
                               ns.RDF,
                               parent_id))
            if parent is not None:
                parent_label = parent.find("{%s}label[@{%s}lang='en']" %\
                                           (ns.RDFS,
                                            ns.XML))
                super_classes.append(get_python_classname(parent_label.text))
        if len(super_classes) < 1:
            super_classes.append(object)
        class_name = get_python_classname(label.text)
        params = {'rdf_ID':rdf_ID,
                  'redis_key': '%s:%s' % (redis_prefix,
                                          class_name)}
        all_prop_xpath = "{%s}Property/{%s}range[@{%s}resource='#%s']" %\
                                     (ns.RDF,
                                      ns.RDFS,
                                      ns.RDF,
                                      rdf_ID)
        all_ranges = rdf.findall(all_prop_xpath)
        properties = []
        for rdf_range in all_ranges:
            rdf_property = rdf_range.getparent()
            prop_name = rdf_property.find("{%s}label[@{%s}lang='en']" %\
                                          (ns.RDFS,
                                           ns.XML))
            if prop_name is not None:
                properties.append(prop_name.text)
##        print("New class %s, properties %s" %\
##              (class_name,properties))
        
        new_class = type('%s' % class_name,
                         (BaseModel,),
                         params)
        setattr(current_module,class_name,new_class)
                        
        
def load_rda_classes(rda_frbr_file,
                     rda_rel_files,
                     redis_prefix,
                     current_module):
    """
    RDA loading function, takes RDA RDF file and a RDA relationship file and 
    creates python classes with properties.
    
    :param rda_frbr_file: FRBR entity RDA RDF file
    :param rda_rel_files: List of RDA Properties RDF files
    :param redis_prefix: Redis Prefix 
    :param current_moduel: Current module
    """
    raw_rda_frbr = open(rda_frbr_file,'rb').read()
    rda_frbr = etree.XML(raw_rda_frbr)
    rda_rels_xml = []
    for filename in rda_rel_files:
        raw_rda_rel = open(filename,'rb').read()
        rda_rel = etree.XML(raw_rda_rel)
        rda_rels_xml.append(rda_rel)
    
    all_desc = rda_frbr.findall("{%s}Description" % ns.RDF)
    for desc in all_desc:
        rda_url = desc.get('{%s}about' % ns.RDF)
        all_properties = []
        for rda_rel in rda_rels_xml:
            rda_properties = rda_rel.findall('{%s}Description/{%s}domain[@{%s}resource="%s"]' % (ns.RDF,
                                                                                                 ns.RDFS,
                                                                                                 ns.RDF,
                                                                                                 rda_url))
            all_properties.extend(rda_properties)
        reg_name = desc.find('{%s}name' % ns.REG)
        if reg_name is not None:
            class_name = reg_name.text
            params = {'redis_key': '%s:%s' % (redis_prefix,
                                              class_name)}
            for prop in all_properties:
                parent = prop.getparent()
                name = parent.find('{%s}name' % ns.REG)
                params[name.text] = None
                #label = parent.find('{%s}label' % ns.RDFS)
                #params[label.text] = None
            #logging.error("Params = %s" % params)
            new_class = type('%s' % class_name,
                             (BaseModel,),
                             params)
            setattr(current_module,class_name,new_class)
         
    
class BaseModel(object):
    """
    :class:`BaseModel` is a lightweight Python wrapper base class for 
    use by various modules in the FRBR Redis Datastore Project. This
    class should not be used directly but should be extended by sub-classes
    depending on its use.
    """
       
    def __init__(self,**kwargs):
        """
        Takes a key and optional Redis server and creates an instance
        in the Redis datastore.

        :param redis_key: Redis Key, required
        :param redis_server: Redis server, if not present will be set the
                             default Redis server.
        """
        if kwargs.has_key("redis_key"):
            self.redis_key = kwargs.pop("redis_key")
        if kwargs.has_key("redis_server"):
            self.redis_server = kwargs.pop("redis_server")
        else:
            self.redis_server = redis_server
        self.redis_ID = self.redis_server.incr("global:%s" % self.redis_key)
        self.frbr_key = "%s:%s" % (self.redis_key,self.redis_ID)
        for k,v in kwargs.iteritems():
            if type(v) == list or type(v) == set:
                new_key = "%s:%s" % (self.frbr_key,k)
                for item in v:
                    self.redis_server.sadd(new_key,item)
                self.redis_server.hset(self.frbr_key,k,new_key)
            else:
                self.redis_server.hset(self.frbr_key,k,v)
            setattr(self,k,v)

    def get_property(self,obj_property):
        """
        Function tries to retrieve the property from the FRBR Redis 
        datastore.
        
        :param obj_property: Required, name of the property
        """
        return self.redis_server.hget(self.frbr_key,obj_property)
          
        
    def get_or_set_property(self,obj_property,entity=None):
        """
        Retrieves property. If entity, adds entity to set
        for the self.frbr_key

        :param obj_property: Required, name of the property
        :param entity: Optional, an entity to add as a set if multiple
                       instances of :class:`BaseModel` property exists 
        """
        existing_properties = self.get_property(obj_property)
        property_key = "%s:%s" % (self.frbr_key,obj_property)
        if entity is not None:
            if existing_properties is not None:
                if self.redis_server.type(existing_properties) == set:
                    self.redis_server.sadd(property_key,
                                           entity)
                else:
                    # Remove property as a singleton and replace with 
                    # a set, adding both existing and new entity
                    self.redis_server.hdel(self.frbr_key,obj_property)
                    property_set_key = "%s_set" % property_key
                    self.redis_server.sadd(property_set_key,existing_properties)
                    self.redis_server.sadd(property_set_key,entity)
                    self.redis_server.hset(self.frbr_key,obj_property,property_set_key)
        return self.get_property(obj_property)

    def set_property(self,obj_property,value):
        """
        Method sets property to value. If obj_property already exists
        and value is de-duped and turned into a set if needed.

        :param obj_property: name of property
        :param value: Value of property
        """
        existing_properties = self.get_property(obj_property)
        if existing_properties is None:
            if type(value) == list:
                if len(value) == 1:
                    self.redis_server.hset(self.frbr_key,
                                           obj_property,
                                           value[0])
                else:
                    new_redis_key = "%s:%s" % (self.frbr_key,
                                               obj_property)
                    for row in value:
                        self.redis_server.sadd(new_redis_key,
                                               row)
                    self.redis_server.hset(self.frbr_key,
                                           obj_property,
                                           new_redis_key)
            else:
                self.redis_server.hset(self.frbr_key,
                                       obj_property,
                                       value)
                
        
        
