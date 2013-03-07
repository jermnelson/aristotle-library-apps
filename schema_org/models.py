__author__ = "Jeremy Nelson"
import json, os
from django.db import models

from aristotle.settings import PROJECT_HOME
from aristotle.settings import ANNOTATION_REDIS, AUTHORITY_REDIS, CREATIVE_WORK_REDIS, INSTANCE_REDIS
from stdnet import odm

SCHEMA_RDFS = json.load(open(os.path.join(PROJECT_HOME,
                                          'schema_org',
                                          'fixures',
                                          'all.json'),
                             'rb'))

class Thing(odm.StdModel):
    """
    Schema.org Thing Base Model available at http://schema.org/Thing
    """
    additionalType = odm.ForeignField()
    description = odm.CharField()
    image = odm.CharField()
    name = odm.SymbolField()
    url = odm.SymbolField()

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True

class CreativeWork(Thing):
    """
    Schema.org Creative Work Model available at http://schema.org/CreativeWork
    """
    about = odm.ForeignField()
    accountablePerson = odm.ForeignField('Person')
    aggregateRating = odm.SymbolField()
    alternativeHeadline = odm.SymbolField()
    associatedMedia = odm.SymbolField()
    audience = odm.SymbolField()
    audio = odm.SymbolField()
    author = odm.SymbolField()
    award = odm.SymbolField()
    awards = odm.SymbolField()
    comment = odm.SymbolField()
    contentLocation = odm.SymbolField()
    contentRating = odm.SymbolField()
    contributor = odm.SymbolField()
    copyrightHolder = odm.SymbolField()
    copyrightYear = odm.SymbolField()
    creator = odm.SymbolField()
    dateCreated = odm.SymbolField()
    dateModified = odm.SymbolField()
    datePublished = odm.SymbolField()
    discussionUrl = odm.SymbolField()
    editor = odm.SymbolField()
    encoding = odm.SymbolField()
    encodings = odm.SymbolField()
    genre = odm.SymbolField()
    headline = odm.SymbolField()
    inLanguage = odm.SymbolField()
    interactionCount = odm.SymbolField()
    isFamilyFriendly = odm.SymbolField()
    keywords = odm.SymbolField()
    mentions = odm.SymbolField()
    offers = odm.SymbolField()
    provider = odm.SymbolField()
    publisher = odm.SymbolField()
    publishingPrinciples = odm.SymbolField()
    review = odm.SymbolField()
    reviews = odm.SymbolField()
    sourceOrganization = odm.SymbolField()
    text = odm.SymbolField()
    thumbnailUrl = odm.SymbolField()
    version = odm.SymbolField()
    video = odm.SymbolField()
        



