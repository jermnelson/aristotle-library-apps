__author__ = "Jeremy Nelson"
import json, os
from stdnet import odm

from aristotle.settings import PROJECT_HOME
from aristotle.settings import ANNOTATION_REDIS, AUTHORITY_REDIS, CREATIVE_WORK_REDIS, INSTANCE_REDIS

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
    audio = odm.CharField()
    author = odm.ManyToManyField()
    award = odm.ListField()
    comment = odm.ManyToManyField('UserComments')
    contentLocation = odm.ForeignField('Place')
    contentRating = odm.SymbolField()
    contributor = odm.ManyToManyField()
    copyrightHolder = odm.ForeignField()
    copyrightYear = odm.DateField()
    creator = odm.ManyToManyField()
    dateCreated = odm.SymbolField()
    dateModified = odm.SymbolField()
    datePublished = odm.SymbolField()
    discussionUrl = odm.SymbolField()
    editor = odm.ForeignField('Person')
    encoding = odm.ForeignField('MediaObject')
    genre = odm.SymbolField()
    headline = odm.CharField()
    inLanguage = odm.SymbolField()
    interactionCount = odm.SymbolField()
    isFamilyFriendly = odm.BooleanField()
    keywords = odm.SetField()
    mentions = odm.ManyToManyField()
    offers = odm.ManyToManyField('Offer')
    provider = odm.ManyToManyField()
    publisher = odm.ManyToManyField()
    publishingPrinciples = odm.CharField()
    review = odm.SymbolField('Review')
    sourceOrganization = odm.ForeignField('Organization')
    text = odm.CharField()
    thumbnailUrl = odm.CharField()
    version = odm.FloatField()
    video = odm.ForeignField('VideoObject')
        


class Person(Base):
    additionalType = odm.SymbolField()
    description = odm.SymbolField()
    image = odm.SymbolField()
    name = odm.SymbolField()
url = odm.SymbolField()
additionalName = odm.SymbolField()
address = odm.SymbolField()
affiliation = odm.SymbolField()
alumniOf = odm.SymbolField()
award = odm.SymbolField()
awards = odm.SymbolField()
birthDate = odm.SymbolField()
brand = odm.SymbolField()
children = odm.SymbolField()
colleague = odm.SymbolField()
colleagues = odm.SymbolField()
contactPoint = odm.SymbolField()
contactPoints = odm.SymbolField()
deathDate = odm.SymbolField()
duns = odm.SymbolField()
email = odm.SymbolField()
familyName = odm.SymbolField()
faxNumber = odm.SymbolField()
follows = odm.SymbolField()
gender = odm.SymbolField()
givenName = odm.SymbolField()
globalLocationNumber = odm.SymbolField()
hasPOS = odm.SymbolField()
homeLocation = odm.SymbolField()
honorificPrefix = odm.SymbolField()
honorificSuffix = odm.SymbolField()
interactionCount = odm.SymbolField()
isicV4 = odm.SymbolField()
jobTitle = odm.SymbolField()
knows = odm.SymbolField()
makesOffer = odm.SymbolField()
memberOf = odm.SymbolField()
naics = odm.SymbolField()
nationality = odm.SymbolField()
owns = odm.SymbolField()
parent = odm.SymbolField()
parents = odm.SymbolField()
performerIn = odm.SymbolField()
relatedTo = odm.SymbolField()
seeks = odm.SymbolField()
sibling = odm.SymbolField()
siblings = odm.SymbolField()
spouse = odm.SymbolField()
taxID = odm.SymbolField()
telephone = odm.SymbolField()
vatID = odm.SymbolField()
workLocation = odm.SymbolField()
worksFor = odm.SymbolField()
