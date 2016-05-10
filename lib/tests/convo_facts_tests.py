import unittest
import sys, json
from lib import calc_graph, convo_fact

class ConvoFactTestCase(unittest.TestCase):

    def test_basic(self):
        data = json.load(open('lib/tests/test.json'))
        protocol = convo_fact.Protocol(data)
        convo_protocol = convo_fact.ConvoProtocol(protocol)
        cg = calc_graph.CG()

if __name__ == '__main__':
    unittest.main()
