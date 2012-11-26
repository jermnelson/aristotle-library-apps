"""
 :mod:`bibframe_models` - Redis and other helper classes for the Bibliographic
 Framework App
"""
__author__ = "Jeremy Nelson"
import redis,datetime
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

    def __init__(self,**kwargs):
        """
        Initializes an object

        :param redis: Redis instance
        :param redis_key: The object's Redis key in the datastore
        """
        if kwargs.has_key('attributes'):
            self.attributes = kwargs.get('attributes')
        else:
            self.attributes = {}
        if kwargs.has_key('redis'):
            self.redis = kwargs.get('redis')
        else:
            self.redis = None
        if kwargs.has_key('redis_key'):
            self.redis_key = kwargs.get('redis_key')
        else:
            self.redis_key = None
            

    def save(self):
        """
        Method adds or saves the object to the Redis datastore,
        should be overridden by child classes save method.
        """
        # Checks if object exists in datastore, if not adds
        # a Redis hash key for the object
        if self.redis_key is not None and self.redis is not None:
            if self.redis.exists(self.redis_key) is False:
                self.attributes['created'] = datetime.datetime.now().isoformat()
            # Iterates through attributes and save values to
            # Redis datastore
	    redis_pipeline = self.redis.pipeline()
            for attrib_key,value in self.attributes.iteritems():
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
                    for nk,nv in value.iteritems():
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
    Annotation class is a high level model in the Bibliographic Framework. It is
    made up of attributes derived from RDA/FRBR and noted as such.
    """

    def __init__(self,**kwargs):
        """
        Creates an Annotation object
        """
        if not kwargs.has_key('redis'):
            kwargs['redis'] = ANNOTATION_REDIS
	if not kwargs.has_key('annotation_key_pattern'):
	    self.annotation_key_pattern = "bibframe:Annotation"
	else:
	    self.annotation_key_pattern = kwargs.get('annotation_key_pattern')
        super(Annotation,self).__init__(**kwargs)

    def save(self):
        """
        Saves the Annotation object to the Redis datastore
        """
        if self.redis_key is None:
	    self.redis_key = "{0}:{1}".format(self.annotation_key_pattern,
		                              self.redis.incr("global {0}".format(self.annotation_key_pattern)))
        super(Annotation,self).save()


class Authority(BibFrameModel):
    """
    Author class is a high level model in the Bibliographic Framework. It is
    made up of attributes derived from RDA/FRBR and noted as such.
    """

    def __init__(self,**kwargs):
        """
        Creates an Annotation object
        """
        if not kwargs.has_key('authority_ds'):
            kwargs['authority_ds'] = AUTHORITY_REDIS
        super(Authority,self).__init__(**kwargs)


class CreativeWork(BibFrameModel):
    """
    Work class is a high level model in the Bibliographic Framework. It is
    made up of attributes derived from RDA/FRBR and noted as such.
    """

    def __init__(self,**kwargs):
        """
        Creates a Work object
        """
        if not kwargs.has_key('redis'):
            kwargs['redis'] = WORK_REDIS
        super(CreativeWork,self).__init__(**kwargs)

    def add_annotation(self,annotation_key):
        """
        Function adds an annotation to the work
        """
        pass

    def save(self):
        """
        Saves the Work object to the Redis datastore
        """
        if self.redis_key is None:
            self.redis_key = "bibframe:CreativeWork:{0}".format(self.redis.incr("global bibframe:CreativeWork"))
        if self.attributes.has_key('bibframe:Instances'):
            self.attributes['bibframe:Instances'] = set(self.attributes['bibframe:Instances'])
        super(CreativeWork,self).save()

class CorporateBody(Authority):

    def save(self):
        if self.redis_key is None:
            self.redis_key = "bibframe:Authority:CorporateBody:{0}".format(self.redis.incr("global bibframe:Authority:CorporateBody"))
        super(Person,self).save()


class Person(Authority):

    def save(self):
        if self.redis_key is None:
            self.redis_key = "bibframe:Authority:Person:{0}".format(self.redis.incr("global bibframe:Authority:Person"))
        super(Person,self).save()



    
        
class Instance(BibFrameModel):
    """
    Instance class is a high level model in the Bibliographic Framework. It is
    made up of attributes derived from RDA/FRBR and noted as such.
    """

    def __init__(self,**kwargs):
        """
        Creates an Instance object
        """
        if not kwargs.has_key('redis'):
            kwargs['redis'] = INSTANCE_REDIS
        super(Instance,self).__init__(**kwargs)

    def save(self):
        """
        Saves the Instance object to the Redis datastore
        """
        if self.redis_key is None:
            self.redis_key = "bibframe:Instance:{0}".format(self.redis.incr("global bibframe:Instance"))
        super(Instance,self).save()
                
    
        




