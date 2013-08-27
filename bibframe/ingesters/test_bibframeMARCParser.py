__author__ = "Jeremy Nelson"

from aristotle.settings import TEST_REDIS
from unittest import TestCase


import bibframeMARCParser as parser

class MARC21toBIBFRAMERegexTest(TestCase):

    def setUp(self):
        pass

    def test_init(self):
        self.assert_(1)
##
##    def test_marc_field_re(self):
##        "Tests MARC_FLD_RE in bibframeMARCParser parser class"
##        first_result = parser.MARC_FLD_RD.search('M0411_b').groupdict()
##        self.assertEquals(first_result.get('tag'),
##                          '041')
##
##    def tearDown(self):
##        TEST_REDIS.flushdb()
        
