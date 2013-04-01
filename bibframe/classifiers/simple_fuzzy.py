"""
  Simple classifer that uses fuzzy matching of Resource's titles and creators to 
  BIBFRAME Works
"""
__author__ = "Jeremy Nelson"
from fuzzywuzzy import fuzz
from bibframe.models import Work, Instance
from title_search.redis_helpers import search_title

class SimpleFuzzyClassifier(object):
    """
    SimpleFuzzyClassifier uses a simple fuzzy match on titles and Creators using
    both BIBFRAME and RDA properties.
    """

    def __init__(self, **kwargs):
        """
        Initalizes an instance of SimpleFuzzyClassifer

        :keyword annotation_ds: Annotation Redis Datastore
        :keyword authority_ds: Authority Redis Datastore
        :keyword creative_work_ds: Creative Work Redis Datstore
        :keyword entity_info: A dictionary of values extracted from a record
        :keyword instance_ds: Instance Redis Datastore
        """
        self.annotation_ds = kwargs.get('annotation_ds', None)
        self.authority_ds = kwargs.get('authority_ds', None)
        self.creative_work_ds = kwargs.get('creative_work_ds', None)
        self.instance_ds = kwargs.get('instance_ds', None)
        self.entity_info = kwargs.get('entity_info', None)


class WorkClassifier(SimpleFuzzyClassifier):
    """
    WorkClassfier uses simple matching to determine if a work is new or
    an existing work in the datastore.
    """

    def __init__(self, **kwargs):
        """
        Initalizes an instance of WorkClassifier

        :keyword creative_work: Existing Work
        :keyword strict: If strict, does an AND intersection, if False does
                         an OR union
        """
        self.creative_work = kwargs.get('creative_work', None)
        self.strict = kwargs.get('strict', True)
        super(WorkClassifier, self).__init__(**kwargs)

    def classify(self):
        """
        Method takes values of an Work and attempts to classify the
        Work as either an existing or new work

        :param work: Creative Work
        """
        if self.entity_info.has_key('title'):
            # Searches Redis
            cw_title_keys = search_title(self.entity_info['title']['rda:preferredTitleForTheWork'],
                                         self.creative_work_ds)
            for creative_wrk_key in cw_title_keys:
                if self.creative_work_ds.hexists(creative_wrk_key,
                                                 'associatedAgent'):
                    creator_keys = set([
                        self.creative_work_ds.hget(creative_wrk_key,
                                                   'associatedAgent')])
                else:
                    creator_keys = self.creative_work_ds.smembers(
                        "{0}:associatedAgent".format(creative_wrk_key))
                if self.entity_info.has_key('rda:isCreatedBy'):
                    if self.strict is True:
                        existing_keys = creator_keys.intersection(self.entity_info['rda:isCreatedBy'])
                    else:
                        existing_keys = creator_keys.union(self.entity_info['rda:isCreatedBy'])
                    if len(existing_keys) == 1:
                        self.creative_work = Work(primary_redis=self.creative_work_ds,
                                                  redis_key=creative_wrk_key)
            if not self.creative_work:
                self.creative_work = Work(primary_redis=self.creative_work_ds)
                for key, value in self.entity_info.iteritems():
                    setattr(self.creative_work,key,value)
        else:
            print("Entity does not have a title {0}".format(self.entity_info))
        
