"""
  Naive Bayes BIBFRAME classifier
"""
__author__ = "Jeremy Nelson"
from aristotle.settings import ANNOTATION_REDIS, AUTHORITY_REDIS 
from aristotle.settings import CREATIVE_WORK_REDIS, INSTANCE_REDIS

class WorkClassifier(object):
    """Naive Baye Work Classifier 

    Class uses conditional probability theory to classifing potential works as
    either a new work or as an existing work.
    """

    def __init__(self, **kwargs):
        """Creates an instance of a Naive Bayes Work Classifier
        

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


