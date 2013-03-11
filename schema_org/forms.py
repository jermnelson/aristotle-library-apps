"""
 :mod:`forms` Forms for performing CRUD operations on BIBFRAME entities populated with schema.org
"""
from wtforms import Form, BooleanField, SelectField, TextField, validators
from bibframe.models import Holding, Instance, Organization, Person, Work
from models import SCHEMA_RDFS

WORK_TYPES = []
for subtype in SCHEMA_RDFS.get('types').get('CreativeWork').get('subtypes'):
    WORK_TYPES.append((subtype, subtype))

ACTIVE_SCHEMA_TYPES = ['Book', 'BlogPosting', 'NewsArticle', 'ScholarlyArticle']

class SchemaOrgTypeNotFoundException(Exception):
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr("{0} not found in schema.org types".format(self.value))
    

def get_dynamic_forms():
    """
    Helper function creates basic forms for adding schema.org data to 
    BIBFRAME Instance, Work, Organization, Person, and Holding
    """
    # Adds the following forms for these specific schema.org Things
    for name in ACTIVE_SCHEMA_TYPES:
        params = get_form_fields(name)
        new_class = type(name,
                         Form,
                         params)
        
    setattr(sys.modules[__name__], name, new_class)

def get_form_fields(schema_type):
    """
    Helper function takes a schema_type and returns a dict of WTForms Fields

    :param schema_type: Name of the schema.org Thing Type    
    """
    params = {}
    if SCHEMA_RDFS.get('types').has_key(schema_type) is False:
        raise SchemaOrgTypeNotFoundException(schema_type)
    for property_name in SCHEMA_RDFS.get('types').get(schema_type).get('properties'):
        if SCHEMA_RDFS.get('properties').has_key(property_name):
            fields = []
            schema_property = SCHEMA_RDFS.get('properties').get(property_name)
            if schema_property.has_key('ranges'):
                for value in schema_property.get('ranges'):
                    fields.append(get_field_by_range(value))
            params[property_name] = fields
    return params
            
def get_field_by_range(value, label=None):
    """
    Helper function returns a Form Field based on the value in the
    range.

    :param value: The value is from the range list in the schema.org
                  Thing properties
    :param label: Label for the Field
    """
    
    if SCHEMA_RDFS.get('datatypes').has_key(value):
        if value == 'Text':
            return TextField(label)
    if SCHEMA_RDFS.get('types').has_key(value):
        schema_type = SCHEMA_RDFS.get('types').get(value)
        if label is None:
            label = schema_type.get('label')
        if len(schema_type.get('instances', [])) > 0:
            instances = [(instance, instance) for instance in schema_type.get('instances')]
            return SelectField(label,
                               choices=instances)
    if label is None:
        label = value
    return TextField(label)
    
            
            
            
    
