"""
 :mod:`redis_helpers` Hours Helper Functions for interacting with Redis
 datastore
"""
__author__ = 'Jon Driscoll, Jeremy Nelson'


import datetime,redis,copy
import aristotle.settings

redis_ds = aristotle.settings.OPERATIONAL_REDIS
library_key_format = 'library-hours:%Y-%m-%d'
time_format = '%H:%M'


def calculate_offset(at_time):
    """
    Helper function takes a datetime and calculates the offset assuming
    a 96 bit string for every quarter hour of a 24 hour day.

    :param at_time: Datetime for calculating the offset
    :rtype: int
    """
    offset = at_time.hour * 4
    if offset is 0:
       offset = 1
    minute = at_time.minute
    if minute > 14 and minute < 30:
        offset += 1 
    elif minute > 29 and minute < 45:
        offset += 2
    elif minute > 44:
	offset += 3
    return offset

def calculate_time(offset,
                   start=True,
                   end=False):
    """
    Helper function takes an offset between 1-96 and returns the
    time based on start and end parameters.

    :param offset: Int between 1-96
    :param start: Boolean, default to True
    :param end: Boolean, default to False
    :rtype: Time
    """
    start_time = {0:0,1:15,2:30,3:45}
    end_time = {0:0,1:30,2:45,3:0}
    hour = offset/4
    remainder = offset%4
    print("{0} {1} {2}".format(offset,hour,remainder))
    if offset < 4:
        hour = offset
    if start is True and end is True:
        return (datetime.time(hour,
                              start_time.get(remainder)),
                datetime.time(hour,
                              end_time.get(remainder)))
    elif start is True and end is False:
        
##        if remainder > 2:
##            return datetime.time(hour+1,
##                                 start)
##        else:
        return datetime.time(hour,
                             start_time.get(remainder))
                                 
    elif start is False and end is True:
        return datetime.time(hour,
                             end_time.get(remainder))
                              
    
    
    
        
    
    return datetime.time(hour,minute)
    
    

def add_library_hours(open_on,
                      close_on,
                      redis_ds=redis_ds):
    """
    Function takes an open and close dates, iterates through each quarter
    hour between the two datetimes, setting those quarter hours with a
    1 bit with a 0 bit being set for times outside the this interval.

    dates involved.

    :param open_on: Datetime of opening time 
    :param close_on: Datetime of closing time
    :param redis_ds: Redis datastore, defaults to module redis_ds
    """
    library_key = open_on.strftime(library_key_format)
    if open_on.day != close_on.day:
        raise ValueError("Add library hours requires open_on and close_on to equal")
    start_offset = calculate_offset(open_on)
    end_offset = calculate_offset(close_on)
    # Each 24 hours has 96 bits that can be set for each quarter hour
    # in that time-span.
    for counter in range(1,97):
        bit_value = 0
        if counter >= start_offset and counter <= end_offset:
            bit_value = 1
        if end_offset < start_offset:
            if counter > end_offset and counter < start_offset:
                bit_value = 0
            else:
                bit_value = 1        
	redis_ds.setbit(library_key,counter,bit_value)

def get_closing_time(question_date,redis_ds=redis_ds):
    date_key = question_date.strftime(library_key_format)
    offset = calculate_offset(question_date)
    if bool(redis_ds.getbit(date_key,96)):
	
        next_day = datetime.datetime(question_date.year,
                                     question_date.month,
                                     question_date.day + 1)
        next_day_key = next_day.strftime(library_key_format)
        for counter in range(1,97):
            if not int(redis_ds.getbit(next_day_key,counter)):
                return calculate_time(counter,False,True)
    else:
        for counter in range(offset,96):
            if not bool(redis_ds.getbit(date_key,counter)):
                return calculate_time(counter-1,False,True)
                        
    

def is_library_open(question_date=datetime.datetime.today(),
                    redis_ds=redis_ds):
    """
    Function checks datastore for open and closing times, returns
    True if library is open.
    
    :param question_date: Datetime object to check datastore, default
                          is the current datetime stamp.
    :param redis_ds: Redis datastore, defaults to module redis_ds
    :rtype: Boolean True or False
    """
    offset = calculate_offset(question_date)
    status_key = question_date.strftime(library_key_format)
    return bool(int(redis_ds.getbit(status_key,offset)))
        
