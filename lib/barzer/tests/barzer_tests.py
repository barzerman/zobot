# pylint: disable=missing-docstring, no-self-use
from __future__ import division, absolute_import
import unittest
import sys
import json
from lib.barzer.barzer_svc import barzer
from lib.barzer.barzer_objects import BeadFactory


class BarzerConnectivityTest(unittest.TestCase):
    def test_basic(self):
        """ uncomment """
        objbarz = BeadFactory.make_beads_from_barz(barzer.get_json('hello world'))
        print >> sys.stderr, "ZZDEBUG >>>\n", '\n'.join(str(x) for x in objbarz), "<<<<<"


class BarzerObjectsTest(unittest.TestCase):
    def test_barz_parse(self):
        barz = json.load(open('lib/barzer/tests/barz.json'))
        objbarz = BeadFactory.make_beads_from_barz(barz)
        print >> sys.stderr, "ZZDEBUG >>>>\n", '\n'.join(str(x) for x in objbarz), "<<<<<"

if __name__ == '__main__':
    unittest.main()
