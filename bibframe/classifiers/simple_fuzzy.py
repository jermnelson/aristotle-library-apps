"""
  Simple classifer that uses fuzzy matching of Resource's titles and creators to 
  BIBFRAME Works
"""
__author__ = "Jeremy Nelson"
import datetime
import logging

from fuzzywuzzy import fuzz
from bibframe.models import Work, Instance
from title_search.redis_helpers import search_title
logger = logging.getLogger(__name__)


class SimpleFuzzyClassifier(object):
    """
    SimpleFuzzyClassifier uses a simple fuzzy match on titles and Creators using
    both BIBFRAME and RDA properties.
    """

    def __init__(self, **kwargs):
        """
        Initalizes an instance of SimpleFuzzyClassifer

        Keywords:
        redis_datastore -- Redis Datastore can be a cluster
        """
        self.redis_ds = kwargs.get('redis_datastore')



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
                                         self.redis_ds)
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
                        msg = "{0} MATCHED {1} to {2}".format(
                            datetime.datetime.utcnow().isoformat(),
                            creative_wrk_key,
                            self.entity_info.get('title').get('rda:preferredTitleForTheWork'))
                        print(msg)
                        logger.info(msg)
                        self.creative_work = Work(primary_redis=self.creative_work_ds,
                                                  redis_key=creative_wrk_key)
            if not self.creative_work:
                self.creative_work = Work(primary_redis=self.creative_work_ds)
                for key, value in self.entity_info.iteritems():
                    setattr(self.creative_work, key, value)
                self.creative_work.save()
        else:
            print("Entity does not have a title {0}".format(self.entity_info))
        
