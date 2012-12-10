__author__ = "Jon Driscoll, Jeremy Nelson"

from django.test import TestCase
from redis_helpers import *
import redis,datetime
from aristotle.settings import TEST_REDIS

test_ds = TEST_REDIS



class AddLibraryHoursTest(TestCase):

    def setUp(self):
        self.midnight = datetime.datetime(2012,05,14,0,0)
        self.standard_open = datetime.datetime(2012,05,14,7,30) # 7:30 am
        self.standard_close = datetime.datetime(2012,05,14,2,0) # 2:00 am
        self.last_minute = datetime.datetime(2012,05,14,23,59)

    def test_different_days(self):
        next_day = datetime.datetime(2012,5,15)
        self.assertRaises(ValueError,
                          add_library_hours,
                          **{'open_on':self.standard_open,
                             'close_on':next_day})

    def test_add_hour_range(self):
        add_library_hours(self.standard_open,
                          self.standard_close,
              redis_ds=test_ds)
        # Tests open at 1:30 am
        #print(test_ds.getbit('library-hours:2012-05-14',6))
        self.assert_(is_library_open(datetime.datetime(2012,5,14,1,30),
                                     redis_ds=test_ds))
        # Test close at 2:30 am
        self.assertFalse(is_library_open(datetime.datetime(2012,5,14,2,30),
                                         redis_ds=test_ds))
        add_library_hours(self.standard_open,
                          self.last_minute,
                          redis_ds=test_ds)
        # Test open at 10 am
        self.assert_(is_library_open(datetime.datetime(2012,5,14,10,00),
                                     redis_ds=test_ds))
        # Test open at 11:45 pm
        self.assert_(is_library_open(datetime.datetime(2012,5,14,23,45),
                                     redis_ds=test_ds))

        # Test open at 11:59 pm
        self.assert_(is_library_open(datetime.datetime(2012,5,14,23,59),
        redis_ds=test_ds))

    def tearDown(self):
        test_ds.flushdb()


class CalculateOffsetTest(TestCase):

    def setUp(self):
        self.early_morning_open = datetime.datetime(2012,11,29,0,33)
        self.early_morning_close = datetime.datetime(2012,11,29,3,5)
        self.midmorning_open = datetime.datetime(2012,11,29,8,47)
        self.midafternoon = datetime.datetime(2012,11,29,15,20)
        self.evening = datetime.datetime(2012,11,29,20,35)


    def test_times(self):
        self.assertEquals(calculate_offset(self.early_morning_open),3)
        self.assertEquals(calculate_offset(self.early_morning_close),12)
        self.assertEquals(calculate_offset(self.midmorning_open),35)
        self.assertEquals(calculate_offset(self.midafternoon),61)
        self.assertEquals(calculate_offset(self.evening),82)

    def tearDown(self):
        test_ds.flushdb()

class CalculateTimeTest(TestCase):

    def setUp(self):
        self.early_morning_close_time = datetime.time(2,0)
        self.early_morning_open_time = datetime.time(7,45)
        self.midafternoon = datetime.time(15,15)
        self.evening = datetime.time(20,30)

    def test_early_morning_close_time(self):
        self.assertEquals(calculate_time(8),
                          self.early_morning_close_time)
##        self.assertEquals(calculate_time(8,False,True),
##                          datetime.time(2))
##        self.assertEquals(calculate_time(8,True,True),
##                          (self.early_morning_close_time,
##                           datetime.time(2)))

    def test_early_morning_open_time(self):
        self.assertEquals(calculate_time(31),
                          self.early_morning_open_time)
##        self.assertEquals(calculate_time(31,False,True),
##                          datetime.time(8))

    def test_midafternoon(self):
        self.assertEquals(calculate_time(61),
                          self.midafternoon)

    def test_evening(self):
        self.assertEquals(calculate_time(82),
                          self.evening)

    def tearDown(self):
        pass


class GetClosingTimeTest(TestCase):


    def setUp(self):
        self.standard_open1 = datetime.datetime(2012, 12, 05, 7, 45)  # 7:45 am
        self.standard_close1 = datetime.datetime(2012, 12, 05, 2, 0)  # 2:00 am
        self.standard_open2 = datetime.datetime(2012, 12, 06, 7, 45)  # 7:45 am
        self.standard_close2 = datetime.datetime(2012, 12, 06, 2, 0)  # 2:00 am
        add_library_hours(self.standard_open1,
            self.standard_close1,
            redis_ds=test_ds)
        add_library_hours(self.standard_open2,
            self.standard_close2,
            redis_ds=test_ds)

    def test_get_closing_time(self):
        self.assertEquals(get_closing_time(datetime.datetime(2012,12,05,15,34),
                                           redis_ds=test_ds),
            datetime.time(2,0))
        self.assertEquals(get_closing_time(datetime.datetime(2012,12,05,3,30),
                                           redis_ds=test_ds),
            datetime.time(2,0))



    def tearDown(self):
        test_ds.flushdb()


class IsLibraryOpenTest(TestCase):

    def setUp(self):
        self.midnight = datetime.datetime(2012,05,14,0,0)
        self.standard_open = datetime.datetime(2012,05,14,7,45) # 7:45 am
        self.standard_close = datetime.datetime(2012,05,14,2,0) # 2:00 am
        add_library_hours(self.standard_open,
              self.standard_close,
              redis_ds=test_ds)
        add_library_hours(datetime.datetime(2012,1,20,7,45),
                          datetime.datetime(2012,1,20,17,0),
                          test_ds)

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


