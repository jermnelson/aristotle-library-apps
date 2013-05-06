"""
  Naive Bayes BIBFRAME classifier

  p(c|x,y) = p(x,y|c)p(c)/p(x,y)

"""
__author__ = "Jeremy Nelson"

from numpy import *
from bibframe.models import Work, Instance

class BayesClassifier(object):
    """
    Navive Bayes BIBFRAME classifer takes likely BIBFRAME entities and 
    assigns conditional probabilities of likelyhood
    """

    def __init__(self, **kwargs):
        """
        Creates a BayesClassifier object

        :kwarg annotation_ds: Annotation Redis Datastore
        :kwarg authority_ds: Authority Redis Datastore
        :kwarg creative_work_ds: Creative Work Datastore
        :kwarg instance_ds: Instance Redis Datastore
        """"
        self.annotation_ds = kwargs.get('annotation_ds', None)
        self.authority_ds = kwargs.get('authority_ds', None)
        self.creative_work_ds = kwargs.get('creative_work_ds', None)
        self.instance_ds = kwargs.get('instance_ds', None)


