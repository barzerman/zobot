import unittest
import sys
from lib.barzer.barzer_svc import barzer

class EntExtTestCase(unittest.TestCase):
    def test_basic(self):
        print >> sys.stderr, "ZZDEBUG >>>", barzer.get_json('hello world'), "<<<<"
