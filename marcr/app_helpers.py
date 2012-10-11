"""
 :mod:`app_helpers` - Redis and other helper classes for the Bibliographic
 Framework App
"""
__author__ = "Jeremy Nelson"
import redis,datetime
try:
    import aristotle.settings as settings
    WORK_REDIS = settings.WORK_REDIS
    INSTANCE_REDIS = settings.INSTANCE_REDIS
    AUTHORITY_REDIS = settings.AUTHORITY_REDIS
    ANNOTATION_REDIS = settings.ANNOTATION_REDIS
    OPERATIONAL_REDIS = settings.OPERATIONAL_REDIS
except ImportError, e:
    redis_host = '0.0.0.0'
    WORK_REDIS = redis.StrictRedis(port=6380)
    INSTANCE_REDIS = redis.StrictRedis(port=6381)
    AUTHORITY_REDIS = redis.StrictRedis(port=6382)
    ANNOTATION_REDIS = redis.StrictRedis(port=6383)
    OPERATIONAL_REDIS = redis.StrictRedis(port=6379)


class MARCRModel(object):
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
            for attrib_key,value in self.attributes.iteritems():
                if type(value) is list:
                    self.redis.lpush("{0}:{1}".format(self.redis_key,
                                                      attrib_key),
                                     value)
                elif type(value) is set:
                    for member in list(value):
                        self.redis.sadd("{0}:{1}".format(self.redis_key,
                                                         attrib_key),
                                    member)
                elif type(value) is dict:
                    new_hash_key = "{0}:{1}".format(self.redis_key,
                                                    attrib_key)
                    for nk,nv in value.iteritems():
                        self.redis.hset(new_hash_key,
                                        nk,
                                        nv)
                else:
                    self.redis.hset(self.redis_key,
                                    attrib_key,
                                    value)

class Annotation(MARCRModel):
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
        super(Annotation,self).__init__(**kwargs)

    def save(self):
        """
        Saves the Annotation object to the Redis datastore
        """
        if self.redis_key is None:
            self.redis_key = "marcr:Annotation:{0}".format(self.redis.incr("global marcr:Annotation"))
        super(Annotation,self).save()


class Authority(MARCRModel):
    """
    Author class is a high level model in the Bibliographic Framework. It is
    made up of attributes derived from RDA/FRBR and noted as such.
    """

    def __init__(self,**kwargs):
        """
        Creates an Annotation object
        """
        if not kwargs.has_key('redis'):
            kwargs['redis'] = AUTHORITY_REDIS
        super(Authority,self).__init__(**kwargs)

class CorporateBody(Authority):

    def save(self):
        if self.redis_key is None:
            self.redis_key = "marcr:Authority:CorporateBody:{0}".format(self.redis.incr("global marcr:Authority:CorporateBody"))
        super(Person,self).save()


class Person(Authority):

    def save(self):
        if self.redis_key is None:
            self.redis_key = "marcr:Authority:Person:{0}".format(self.redis.incr("global marcr:Authority:Person"))
        super(Person,self).save()



    
        
class Instance(MARCRModel):
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
            self.redis_key = "marcr:Instance:{0}".format(self.redis.incr("global marcr:Instance"))
        super(Instance,self).save()
                

class Work(MARCRModel):
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
        super(Work,self).__init__(**kwargs)

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
            self.redis_key = "marcr:Work:{0}".format(self.redis.incr("global marcr:Work"))
        if self.attributes.has_key('marcr:Instances'):
            self.attributes['marcr:Instances'] = set(self.attributes['marcr:Instances'])
        super(Work,self).save()


            
        
        

    
        




