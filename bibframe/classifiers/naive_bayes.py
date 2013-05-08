"""
  Naive Bayes BIBFRAME classifier

  p(c|x,y) = p(x,y|c)p(c)/p(x,y)

"""
__author__ = "Jeremy Nelson"
from numpy import *
from bibframe.models import Work, Instance
from aristotle.settings import ANNOTATION_REDIS, AUTHORITY_REDIS 
from aristotle.settings import CREATIVE_WORK_REDIS, INSTANCE_REDIS

class BayesClassifier(object):
    """
    Navive Bayes BIBFRAME classifer takes likely BIBFRAME entities and 
    assigns conditional probabilities of likelyhood
    """

    def __init__(self, **kwargs):
        """Creates a BayesClassifier object

        Keyword arguments:
        annotation_ds -- Annotation Redis Datastore, defaults to settings
        authority_ds -- Authority Redis Datastore, defaults to settings
        creative_work_ds -- Creative Work Redis Datastore. defaults to settings
        instance_ds -- Instance Redis Datastore, defaults to settings
        """
        self.annotation_ds = kwargs.get('annotation_ds', ANNOTATION_REDIS)
        self.authority_ds = kwargs.get('authority_ds', AUTHORITY_REDIS)
        self.creative_work_ds = kwargs.get('creative_work_ds', CREATIVE_WORK_REDIS)
        self.instance_ds = kwargs.get('instance_ds', INSTANCE_REDIS)
        self.operational_ds = kwargs.get('operational_ds', OPERATIONAL_REDIS)
        self.entity_info = kwargs.get('entity_info', {})
        self.data_set = []

    def load_dataset(self):
        "Method should be overloaded by implementing child classes."
        pass

class WorkClassifier(BayesClassifier):
    """Naive Baye Work Classifier 

    Class uses conditional probability theory for classifing potential works as
    either a new work or as an existing work.
    """

    def __init__(self, **kwargs):
        "Creates an instance of a Naive Bayes Work Classifier"
        super(self, WorkClassifer).__init__(**kwargs)


    def load_dataset(self):
        """Loads a bit-count for each existing Creative Work 

        The title and creator name string.

        Bit count for each title and author term
        """ 
        row = list()
        if 'title' not in self.entity_info:
            pass
        else:
            row.append(self.entity_info.get('title')
            for creator_key in self.entity_info.get('author'):
                row.append(self.authority_ds.hget(creator_key, 'name'))     
            self.data_set.append(row)
           

    def generate_work_labels(self, is_manual=False):
        """Generates a vector of booleans one for each row in the dataset

        Keywork arguments:
        is_manual -- Manually prompting, default is False
        """
        pass
