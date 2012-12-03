###############################################################################
# Title Search Unit Tests
#
###############################################################################
__author__ = "Jeremy Nelson"

from django.test import TestCase
from aristotle.settings import TEST_REDIS
from redis_helpers import *
import bibframe.bibframe_models as models

test_ds = TEST_REDIS


class AddOrGetTitleTest(TestCase):

    def setUp(self):
        self.old_man_keys = add_or_get_title('The Old Man in the Sea',
            test_ds)
        print(test_ds.keys("*"))

    def test_old_man_in_sea(self):
        for key in self.old_man_keys:
            self.assert_(test_ds.exists(key))
        self.assert_(test_ds.sismember('all-metaphones:0', 'rda:Title:1'))
        self.assert_(test_ds.sismember('all-metaphones:ALT', 'rda:Title:1'))
        self.assert_(test_ds.sismember('all-metaphones:AN', 'rda:Title:1'))
        self.assert_(test_ds.sismember('all-metaphones:MN', 'rda:Title:1'))
        self.assert_(test_ds.sismember('all-metaphones:S', 'rda:Title:1'))
        self.assert_(test_ds.sismember('title-metaphones:0ALTMNAN0S',
            'rda:Title:1'))

    def tearDown(self):
        test_ds.flushdb()


class AddTitleTest(TestCase):

    def setUp(self):
        self.colorado_metaphones = process_title('Colorado')[2]
        self.colorado_key = add_title('Colorado',
            self.colorado_metaphones,
            test_ds)

    def test_colorado_title(self):
        self.assert_(test_ds.exists(self.colorado_key))
        self.assertEquals(test_ds.hget(self.colorado_key, 'phonetic'),
            'KLRT')
        self.assertEquals(test_ds.hget(self.colorado_key, 'raw'),
            'Colorado')

    def tearDown(self):
        test_ds.flushdb()


class GenerateTitleApp(TestCase):

    def setUp(self):
        self.creative_work = models.CreativeWork()




