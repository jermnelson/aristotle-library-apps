"""
  Simple classifer that uses fuzzy matching of Resource's titles and creators to 
  BIBFRAME Works
"""
__author__ = "Jeremy Nelson"
import datetime
import logging

from fuzzywuzzy import fuzz
from bibframe.models import Article, Audio, Book, Globe, Jurisdiction
from bibframe.models import Legislation, Manuscript, Map, MixedMaterial
from bibframe.models import MovingImage, NonmusicalAudio, NotatedMovement
from bibframe.models import NotatedMusic, RemoteSensingImage, Serial
from bibframe.models import SoftwareOrMultimedia, StillImage, Tactile
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
        self.redis_datastore = kwargs.get('redis_datastore')



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
        self.work_class = kwargs.get('work_class', Work)
        self.entity_info = kwargs.get('entity_info', {})
        self.strict = kwargs.get('strict', True)
        
        super(WorkClassifier, self).__init__(**kwargs)

    def classify(self):
        "method attempts to classify a Work as either an existing or new work"
        if self.entity_info.has_key('title'):
            # Searches Redis
            redis_title = self.entity_info['title']
            # Returns a label if redis_title is a bf:TitleEntity
            title_label = self.redis_datastore.hget(
                redis_title,
                'label')
            if title_label is None:
                # Sets by retrieving the literal title value
                title_label = redis_title
            if title_label is not None:
                print("Title is {0}".format(title_label))
                cw_title_keys = search_title(title_label,
                                             self.redis_datastore)
            print("Creative work keys={0}".format(cw_title_keys))
            for creative_wrk_key in cw_title_keys:
                if not creative_wrk_key.name.startswith(self.class_name.name):
                    continue
                if self.redis_datastore.hexists(creative_wrk_key,
                                                'associatedAgent'):
                    creator_keys = set([
                        self.redis_datastore.hget(creative_wrk_key,
                                                   'associatedAgent')])
                else:
                    creator_keys = self.redis_datastore.smembers(
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
                            self.entity_info.get('title'))
                        print(msg)
                        logger.info(msg)
                        self.creative_work = self.work_class(redis_datastore=self.redis_datastore,
                                                             redis_key=creative_wrk_key)
            if not self.creative_work:
                self.creative_work = self.work_class(redis_datastore=self.redis_datastore)
                for key, value in self.entity_info.iteritems():
                    setattr(self.creative_work, key, value)
                self.creative_work.save()
        else:
            print("Entity does not have a title {0}".format(self.entity_info))
        
