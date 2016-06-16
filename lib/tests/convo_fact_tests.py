# pylint: disable=invalid-name, missing-docstring
import unittest
import pprint
import json
from lib import calc_graph, convo_fact

pp = pprint.PrettyPrinter()


class ConvoTestCase(unittest.TestCase):

    def test_flu(self):
        pp = pprint.PrettyPrinter()
        data = json.load(open('lib/tests/test2.json'))
        convo_protocol = convo_fact.ConvoProtocol(data)
        cg = calc_graph.CG()
        cg.root = convo_protocol
        pp.pprint(cg.root.to_dict())

        print cg.step()
        print cg.step('220')
        pp.pprint(cg.root.to_dict())
        resp = cg.step('yes')
        self.assertTrue('flu' in resp[1].text)
        pp.pprint(cg.root.to_dict())

    def test_911(self):
        pp = pprint.PrettyPrinter()
        data = json.load(open('lib/tests/test2.json'))
        convo_protocol = convo_fact.ConvoProtocol(data)
        cg = calc_graph.CG()
        cg.root = convo_protocol
        pp.pprint(cg.root.to_dict())

        print cg.step()
        print cg.step('190')
        print cg.root.to_dict()
        print cg.root.index
        resp = cg.step('140')
        print resp
        pp.pprint(cg.root.to_dict())
        resp = cg.step('140')
        print resp
        self.assertTrue('911' in resp[1].text)


if __name__ == '__main__':
    unittest.main()
