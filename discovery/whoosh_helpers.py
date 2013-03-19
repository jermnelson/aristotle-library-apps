"""
 Implements a Whoosh Search for Discovery App
"""
__author__ = "Jeremy Nelson"

from whoosh.fields import SchemaClass, DATETIME, TEXT, KEYWORD, ID, STORED

class CreativeWorkSchema(SchemaClass):
    """
    Whoosh Schema for a BIBFRAME Creative Work
    """
    title = TEXT(stored=True)
    work_key = ID(stored=True)
    
