"""
 :mod:`bibframe_models` - Redis and other helper classes for the Bibliographic
 Framework App
"""
__author__ = "Jeremy Nelson"

import redis
import datetime
from aristotle.redis_helpers import generate_redis_protocal

try:
    import aristotle.settings as settings
    CREATIVE_WORK_REDIS = settings.CREATIVE_WORK_REDIS
    INSTANCE_REDIS = settings.INSTANCE_REDIS
    AUTHORITY_REDIS = settings.AUTHORITY_REDIS
    ANNOTATION_REDIS = settings.ANNOTATION_REDIS
    OPERATIONAL_REDIS = settings.OPERATIONAL_REDIS
except ImportError, e:
    redis_host = '0.0.0.0'
    CREATIVE_WORK_REDIS = redis.StrictRedis(port=6380)
    INSTANCE_REDIS = redis.StrictRedis(port=6381)
    AUTHORITY_REDIS = redis.StrictRedis(port=6382)
    ANNOTATION_REDIS = redis.StrictRedis(port=6383)
    OPERATIONAL_REDIS = redis.StrictRedis(port=6379)


class BibFrameModel(object):
    """
    Base class for all classes of the Bibliographic Framework's High level
    models
    """

    def __init__(self, **kwargs):
        """
        Initializes an object

        :param redis: Redis instance
        :param redis_key: The object's Redis key in the datastore
        """
        if 'attributes' in kwargs:
            self.attributes = kwargs.get('attributes')
        else:
            self.attributes = {}
        if 'redis' in kwargs:
            self.redis = kwargs.get('redis')
        else:
            self.redis = None
        if 'redis_key' in kwargs:
            self.redis_key = kwargs.get('redis_key')
        else:
            self.redis_key = None
        if 'protocal' in kwargs:
            self.protocal_file = kwargs.get('protocal')
        self.redis_output = None

    def generate_redis_protocal(self, *args):
        """
        Helper function generates Redis Protocal
        """
        proto = generate_redis_protocal(*args)
        if self.redis_output is not None:
            self.redis_output.write(proto)

    def save_protocal(self):
        """
        Creates a Redis Protocal file
        """
        self.redis_output = open(self.protocal_filepath, 'ab')
        if self.redis_key is not None and self.redis is not None:
            if self.redis.exists(self.redis_key) is False:
                self.attributes['created'] = \
                datetime.datetime.utcnow().isoformat()
            for attrib_key, value in self.attributes.iteritems():
                redis_attrib_key = "{0}:{1}".format(self.redis_key,
                    attrib_key)
                if type(value) is list:
                    self.generate_redis_protocal("LPUSH",
                        redis_attrib_key,
                        value)
                elif type(value) is set:
                    for member in list(value):
                        self.generate_redis_protocal("SADD",
                            redis_attrib_key,
                            member)
                elif type(value) is dict:
                    for nk, nv in value.iteritems():
                        self.generate_redis_protocal("HSET",
                            redis_attrib_key,
                            nk,
                            nv)
                else:
                    self.generate_redis_protocal("HSET",
                        self.redis_key,
                        attrib_key,
                        value)
        self.redis_output.close()

    def save(self):
        """
        Method adds or saves the object to the Redis datastore,
        should be overridden by child classes save method.
        """
        # Checks if object exists in datastore, if not adds
        # a Redis hash key for the object
        if self.redis_key is not None and self.redis is not None:
            if self.redis.exists(self.redis_key) is False:
                self.attributes['created'] = \
                datetime.datetime.now().isoformat()
            # Iterates through attributes and save values to
            # Redis datastore
            redis_pipeline = self.redis.pipeline()
            for attrib_key, value in self.attributes.iteritems():
                if type(value) is list:
                    redis_pipeline.lpush("{0}:{1}".format(self.redis_key,
                                                          attrib_key),
                                     value)
                elif type(value) is set:
                    for member in list(value):
                        redis_pipeline.sadd("{0}:{1}".format(self.redis_key,
                                                             attrib_key),
                                    member)
                elif type(value) is dict:
                    new_hash_key = "{0}:{1}".format(self.redis_key,
                                                    attrib_key)
                    for nk, nv in value.iteritems():
                        redis_pipeline.hset(new_hash_key,
                                            nk,
                                            nv)
                else:
                    redis_pipeline.hset(self.redis_key,
                                        attrib_key,
                                        value)
            redis_pipeline.execute()


class Annotation(BibFrameModel):
    """
    Annotation class is a high level model in the Bibliographic Framework. It
    is made up of attributes derived from RDA/FRBR and noted as such.
    """

    def __init__(self, **kwargs):
        """
        Creates an Annotation object
        """
        if not 'redis' in kwargs:
            kwargs['redis'] = ANNOTATION_REDIS
        if not 'annotation_key_pattern' in kwargs:
            self.annotation_key_pattern = "bibframe:Annotation"
        else:
            self.annotation_key_pattern = kwargs.get('annotation_key_pattern')
        super(Annotation, self).__init__(**kwargs)

    def save(self):
        """
        Saves the Annotation object to the Redis datastore
        """
        if self.redis_key is None:
            self.redis_key = "{0}:{1}".format(self.annotation_key_pattern,
                self.redis.incr("global {0}".format(
                    self.annotation_key_pattern)))
        super(Annotation, self).save()

class Authority(BibFrameModel):
    """
    Author class is a high level model in the Bibliographic Framework. It is
    made up of attributes derived from RDA/FRBR and noted as such.
    """

    def __init__(self, **kwargs):
        """
        Creates an Annotation object
        """
        if not 'authority_ds' in kwargs:
            kwargs['authority_ds'] = AUTHORITY_REDIS
        super(Authority, self).__init__(**kwargs)


class CreativeWork(BibFrameModel):
    """
    Work class is a high level model in the Bibliographic Framework. It is
    made up of attributes derived from RDA/FRBR and noted as such.
    """

    def __init__(self, **kwargs):
        """
        Creates a Work object
        """
        if not 'redis' in kwargs:
            kwargs['redis'] = CREATIVE_WORK_REDIS
        super(CreativeWork, self).__init__(**kwargs)

    def add_annotation(self, annotation_key):
        """
        Function adds an annotation to the work
        """
        pass

    def save(self):
        """
        Saves the Work object to the Redis datastore
        """
        if self.redis_key is None:
            self.redis_key = "bibframe:CreativeWork:{0}".format(
                self.redis.incr("global bibframe:CreativeWork"))
        if 'bibframe:Instances' in self.attributes:
            self.attributes['bibframe:Instances'] = \
            set(self.attributes['bibframe:Instances'])
        super(CreativeWork, self).save()


class CorporateBody(Authority):

    def save(self):
        if self.redis_key is None:
            self.redis_key = "bibframe:Authority:CorporateBody:{0}".format(
                self.redis.incr("global bibframe:Authority:CorporateBody"))
        super(CorporateBody, self).save()

class Facet(Annotation):
    """
    Facet class is an BIBFRAME `Annotation` that can be associated with either
    a BIBFRAME `CreativeWork` or `Instance`
    """

    def __init__(self, **kwargs):
        """
        Creates a Facet object
        """
        if not 'redis' in kwargs:
            kwargs['redis'] = ANNOTATION_REDIS
        super(Facet, self).__init__()


class Instance(BibFrameModel):
    """
    Instance class is a high level model in the Bibliographic Framework. It is
    made up of attributes derived from RDA/FRBR and noted as such.
    """

    def __init__(self, **kwargs):
        """
        Creates an Instance object
        """
        if not 'redis' in kwargs:
            kwargs['redis'] = INSTANCE_REDIS
        super(Instance, self).__init__(**kwargs)

    def save(self):
        """
        Saves the Instance object to the Redis datastore
        """
        if self.redis_key is None:
            self.redis_key = "bibframe:Instance:{0}".format(
                self.redis.incr("global bibframe:Instance"))
        super(Instance, self).save()

class Person(Authority):

    def save(self):
        if self.redis_key is None:
            self.redis_key = "bibframe:Authority:Person:{0}".format(
                self.redis.incr("global bibframe:Authority:Person"))
        super(Person, self).save()

