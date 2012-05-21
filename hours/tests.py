__author__ = "Jon Driscoll, Jeremy Nelson"

from django.test import TestCase
from redis_helpers import *
import redis,datetime

test_ds = redis.StrictRedis()

class AddLibraryHoursTest(TestCase):

    def setUp(self):
        self.midnight = datetime.datetime(2012,05,14,0,0)
        self.standard_open = datetime.datetime(2012,05,14,7,30) # 7:30 am
        self.standard_close = datetime.datetime(2012,05,14,2,0) # 2:00 am
        self.last_minute = datetime.datetime(2012,05,14,23,59)

    def test_wrong_order(self):
        self.assertRaises(ValueError,
                          add_library_hours,
                          **{'open_on':self.standard_close,
                             'close_on':self.midnight})

    def test_different_days(self):
        next_day = datetime.datetime(2012,5,15)
        self.assertRaises(ValueError,
                          add_library_hours,
                          **{'open_on':self.standard_open,
                             'close_on':next_day})

    def test_add_hour_range(self):
        add_library_hours(self.midnight,
                          self.standard_close)
        
        # Tests open at 1:30 am
        self.assert_(is_library_open(datetime.datetime(2012,5,14,1,30)))
        # Test close at 2:30 am
        self.assertFalse(is_library_open(datetime.datetime(2012,5,14,2,30)))
        add_library_hours(self.standard_open,
                          self.last_minute)
        # Test open at 10 am
        self.assert_(is_library_open(datetime.datetime(2012,5,14,10,00)))
        # Test open at 11:45 pm
        self.assert_(is_library_open(datetime.datetime(2012,5,14,23,45)))

    def tearDown(self):
        test_ds.flushdb()

    

class IsLibraryOpenTest(TestCase):

    def setUp(self):
        self.midnight = datetime.datetime(2012,05,14,0,0)
        self.standard_open = datetime.datetime(2012,05,14,7,30) # 7:30 am
        self.standard_close = datetime.datetime(2012,05,14,2,0) # 2:00 am
        self.standard_key = '%s:open' % self.standard_open.strftime(library_key_format)
        first_range_key = "%s:%s" % (self.standard_key,
                                     test_ds.incr('global:%s' % self.standard_key))
        # Sets first open range from midnight to 2am
        test_ds.zadd(first_range_key,
                     0,
                     self.midnight.strftime(time_format))
        test_ds.zadd(first_range_key,
                     0,
                     self.standard_close.strftime(time_format))
        # Sets second open range from 7:30am to 11:59
        last_minute = datetime.datetime(2012,05,14,23,59)
        second_range_key = "%s:%s" % (self.standard_key,
                                      test_ds.incr('global:%s' % self.standard_key))
        test_ds.zadd(second_range_key,
                     0,
                     self.standard_open.strftime(time_format))
        test_ds.zadd(second_range_key,
                     0,
                     last_minute.strftime(time_format))
        self.holiday_open = datetime.datetime(2012,1,20,7,34)   # 7:45 am
        self.holiday_close = datetime.datetime(2012,1,20,17,00) # 5:00 pm
        self.holiday_key = '%s:open:1' % self.holiday_open.strftime(library_key_format)
        test_ds.zadd(self.holiday_key,
                     0,
                     self.holiday_open.strftime(time_format))
        test_ds.zadd(self.holiday_key,
                     0,
                     self.holiday_close.strftime(time_format))

    def test_standard_day(self):
        """
        Tests standard school day of library closing at 2am and reopening
        at 7:30am
        """
        test_open = datetime.datetime(2012,05,14,12,30)
        test_close = datetime.datetime(2012,05,14,3,47)
        self.assert_(is_library_open(test_open,test_ds))
        self.assertFalse(is_library_open(test_close,test_ds))

    def test_nonexistent_days(self):
        """
        Tests for days that doesn't exist in datastore, assumes that the
        library is closed if the library-hours redis key cannot be found in
        the datastore.
        """
        future_test = datetime.datetime(3000,5,3)
        self.assertFalse(is_library_open(future_test,test_ds))
        past_test = datetime.datetime(1905,9,24)
        self.assertFalse(is_library_open(past_test,test_ds))
                     

    def test_holiday(self):
        """
        Tests holiday schedule when school is not in session. Library opens
        at 7:45 am and closes at 5:00 pm.
        """
        test_open = datetime.datetime(2012,1,20,13,35) # 1:35 pm
        test_close = datetime.datetime(2012,1,20,6,0) #  6:00 am
        test_close2 = datetime.datetime(2012,1,20,18,20) # 6:20 pm
        self.assert_(is_library_open(test_open,test_ds))
        self.assertFalse(is_library_open(test_close,test_ds))        
        self.assertFalse(is_library_open(test_close2,test_ds))

    def tearDown(self):
        test_ds.flushdb()


