# pylint: disable=invalid-name, missing-docstring
import unittest
import pprint
import json
from lib import calc_graph, convo_fact

pp = pprint.PrettyPrinter()


class ConvoFactTestCase(unittest.TestCase):

    def test_flu(self):
        data = json.load(open('lib/tests/test.json'))
        convo_protocol = convo_fact.ConvoProtocol(data)
        cg = calc_graph.CG()
        cg.root = convo_protocol

        print cg.root.step()
        print cg.root.step('I have a temperature 40')
        pp.pprint(cg.root.to_dict())
        resp = cg.root.step('Yes, I have a headache')
        self.assertTrue('flu' in resp.text)


if __name__ == '__main__':
    unittest.main()
