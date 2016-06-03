# pylint: disable=unused-import
import json
import sys
from lib import calc_graph
from lib import cg_ent_fact
from lib.barzer.barzer_svc import barzer
from lib.barzer import barzer_objects
class Runner(object):
    DEFAULT_DATA = {
        'temperature': {
            'class': 459,
            'subclass': 9,
            'id': 'temperature',
            'name': 'Temperature',
            'expression': {'op': '>', 'values': 200},
            'node_id': 'node.temperature',
            'value_type': {
                'type': 'number',
                'lo': 50,
                'hi': 350,
            }
        }
    }
    def __init__(self, fname=None, data=None):
        if not data and not fname:
            raise ValueError('either `fname` or `data` must be not None')

        if not data:
            data = json.load(open(fname))
        self.cg = calc_graph.CG(data)

    def run(self):
        print >> sys.stderr, self.cg.greeting()
        while True:
            line = raw_input('>')
            x = self.cg.step(line)
            print >> sys.stderr, x

        print >> sys.stderr, self.cg.bye()
