"""
  :mod:`rda_core` -- RDA Redis set-up and support
"""
__author__ = 'Jeremy Nelson'

import redis,urllib2,sys,os
from lxml import etree
import namespaces as ns
from common import BaseModel


def setup_rda_core(rda_core_schema_file):
    """
    Setup RDA Core classes for use in the FRBR-Redis datastore project

    :param rda_core_schema_file:
    """
    raw_schema = open(rda_core_schema_file,'rb')
    schema_xml = raw_schema.read()
    raw_schema.close()
    schema_doc = etree.XML(schema_xml)
    # Use xpath to extract all of the complexTypes from the root element
    # We will use the name of the complexType element as the class name
    complexTypes = schema_doc.findall('{%s}complexType' % ns.SCHEMA)
    for entity in complexTypes:
        class_name = entity.attrib['name']
        class_params = {'redis_key':'frbr_rda:%s' % class_name}
        properties = entity.findall('{%s}sequence/{%s}element' % (ns.SCHEMA,ns.SCHEMA))
        # Iterate through all of the element children of the complexType to
        # extract all of the rda properties for this entity class
        for row in properties:
            # Quick hack to remove redundant rda prefix for properties
            class_params[row.attrib['name'].replace('rda','')] = None
        new_class = type('%s' % class_name,
                         (BaseModel,),
                         class_params)
        setattr(current_module,class_name,new_class)
            
        
current_module = sys.modules[__name__]
current_dir = os.path.abspath(os.path.dirname(__file__))
fixures_root = os.path.join(os.path.split(current_dir)[0],
                            'fixures')
schema_filepath = os.path.join(fixures_root,
                               'rdaCore_10_13_09.xsd')
setup_rda_core(schema_filepath)
        
        
    
    
