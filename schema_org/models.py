"""
 Python Models for Schema.org entities
"""
__author__ = "Jeremy Nelson"

import os
import sys
import xml.etree.ElementTree as etree

from backends import RedisStorage

PROJECT_HOME = os.path.abspath(os.path.dirname(__file__))

try:
    from rdflib import RDF, RDFS, OWL
except ImportError:
    OWL = ''
    RDF = ''
    RDFS = ''

SCHEMA_OWL = etree.parse(os.path.join(
    PROJECT_HOME,
    "fixures",
    "schemaorg.owl"))

class SchemaBase(object):

    def __init__(self, storage=None):
        """Base object for Schema.org using a plug-in data
        server and storage

        :param storage: Storage backend, default is None
        """
        self.storage = storage

    def save(self):
        """Method saves the current state of the object to the
        storage backend."""
        if self.storage is not None:
            self.storage.save(self)

def add_properties(schema_dict):
    # Extracts and saves all unique schema.org class properties
    for owl_element_name  in ['DatatypeProperty',
                              'ObjectProperty']:
        properties = SCHEMA_OWL.findall(
            "{{{0}}}{1}".format(OWL,
                                owl_element_name))
        for row in properties:
            property_name = row.attrib['{{{0}}}about'.format(RDF)].split(
                "/")[-1]
            descriptions = row.findall(
                "{{{0}}}domain/{{{1}}}Class/{{{1}}}unionOf/{{{2}}}Description".format(
                    RDFS,
                    OWL,
                    RDF))
            for desc in descriptions:
                class_name = desc.attrib['{{{0}}}about'.format(RDF)].split("/")[-1]
                if not 'properties' in schema_dict[class_name]:
                    print("ERROR {0} should have properties".format(schema_dict[class_name]))
                if not property_name in schema_dict[class_name]['properties']:
                    schema_dict[class_name]['properties'].append(property_name)
    # Adds all parent class properties to each class
    for key in schema_dict.keys():
        if 'parent' in schema_dict[key]:
            parent = schema_dict[key].get('parent')
            if 'properties' in schema_dict[parent]:
                schema_dict[key]['properties'].extend(schema_dict[parent]['properties'])
        for property_name in schema_dict[key]['properties']:
            for child in schema_dict[key]['children']:
                if not property_name in schema_dict[child]['properties']:
                    schema_dict[child]['properties'].append(property_name)
    return schema_dict


def get_classes():
    """
    Extracts classes from schemaorg.owl fixure
    """
    schema_dict = {}
    schema_classes = SCHEMA_OWL.findall(
        "{{{0}}}Class".format(OWL))
    for row in schema_classes:
        about = row.attrib['{{{0}}}about'.format(RDF)]
        name = about.split("/")[-1]
        doc_string = "{0} - URL is {1}\n{2}".format(
            name,
            about,
            row.find("{{{0}}}comment".format(RDFS)).text)
        if name in schema_dict:
            if not 'properties' in schema_dict[name]:
                schema_dict[name]['properties'] = []
            if not '__doc__' in schema_dict[name]:
                schema_dict[name]['__doc__'] = doc_string
        else:
            schema_dict[name] = {'children': [],
                                 'properties': [],
                                 '__doc__': doc_string}
        subClassOf = row.find("{{{0}}}subClassOf".format(RDFS))
        if subClassOf is not None:
            parent = subClassOf.attrib['{{{0}}}resource'.format(RDF)]
            parent_name = parent.split("/")[-1]
            schema_dict[name]['parent'] = parent_name
            if parent_name in schema_dict:
                schema_dict[parent_name]['children'].append(name)
            else:
                schema_dict[parent_name] = {'url': parent, 'children': [name,]}
    return schema_dict


def load_owl():
    """
    Loads schemaorg.owl file and creates lightweight Python objects for each owl:Class
    """
    schema_classes = add_properties(get_classes())
    for name in schema_classes.keys():
        
        parent_class = object
        if 'parent' in schema_classes[name] and  hasattr(sys.modules[__name__],
                                                         schema_classes[name]['parent']): 
            parent_class = getattr(sys.modules[__name__],
                                   schema_classes[name]['parent'])
        attributes = {'__doc__': schema_classes[name].get('__doc__')}
        for row in schema_classes[name].get('properties', []):
            attributes[row] = None
        new_class = type(name,
                         (parent_class,),
                         attributes)
        setattr(sys.modules[__name__],
                name,
                new_class)

load_owl()
