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
        for offset in range(0,97):
            if not bool(redis_ds.getbit(next_day_key,offset)):
                closed_offset = offset
                break
    else:
        for counter in range(offset,96):
            if not bool(redis_ds.getbit(date_key,counter)):
                closed_offset = 
                        
    

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
        
