"""
 :mod:`redis_helpers` Hours Helper Functions for interacting with Redis
 datastore
"""
__author__ = 'Jon Driscoll, Jeremy Nelson'


import datetime,redis,copy

redis_ds = redis.StrictRedis()
library_key_format = 'library-hours:%Y-%m-%d'
time_format = '%H:%M'

def add_library_hours(open_on,
                      close_on,
                      redis_ds=redis_ds):
    """
    Function creates a sorted set with opening time and closing time
    using the following key structure:
      library-hours:{YYYY}-{MM}-{DD}:open:{global.incr}

    :param open_on: Datetime of opening time 
    :param close_on: Datetime of closing time
    :param redis_ds: Redis datastore, defaults to module redis_ds
    """
    if open_on > close_on:
        raise ValueError("Open time of %s cannot be larger than %s" %\
                         (open_on.isoformat(),
                          close_on.isoformat()))
    if open_on.day != close_on.day:
        raise ValueError("open_on.day=%s and close_on.day=%s must be equal" %\
                         (open_on.day,close_on.day))
    library_key = '%s:open:%s' % (open_on.strftime(library_key_format),
                                  redis_ds.incr("global:%s" % library_key_format))
    redis_ds.zadd(library_key,
                  0,
                  open_on.strftime(time_format))
    redis_ds.zadd(library_key,
                  0,
                  close_on.strftime(time_format))
    
      

def is_library_open(question_date=datetime.datetime.today(),
                    redis_ds=redis_ds):
    """
    Function checks datastore for open and closing times, returns
    True if library is open.
    
    :param question_date: Datetime object to check datastore, default
                          is the current datetime stamp.
    :param redis_ds: Redis datastore, defaults to module redis_ds
    """
    status_key = question_date.strftime(library_key_format)
    open_range_keys = redis_ds.keys('%s:open:*' % status_key)
    current_time = question_date.strftime(time_format)
    for range_key in open_range_keys:
        range_set = redis_ds.zrange(range_key,0,-1)
        if range_set[0] <= current_time <= range_set[1]:
            return True
    return False
        
