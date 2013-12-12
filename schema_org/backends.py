__author__ = "Jeremy Nelson"

class Storage(object):
    """Base class for Storage class"""

    def save(self):
        """Save stub method, should be overridden by specific storage
        backends"""
        pass

class RedisStorage(Storage):
    """:class:`RedisStorage` provides a Redis storage backend for
    specific types of metadata backends"""

    def __init__(self, redis_datastore):
        """Initializes :class:`RedisStorage` object.

        :param redis_dataserver: Redis dataserver
        """
        self.redis_datastore = redis_datastore

    def save(self, target_object=None):
        """Saves target object to redis datastore

        :param target_object: Target Object
        """
        pass
