import unittest
import json
from lib import calc_graph, convo_fact
import pprint

pp = pprint.PrettyPrinter()


class ConvoFactTestCase(unittest.TestCase):

    def test_basic(self):
        data = json.load(open('lib/tests/test.json'))
        protocol = convo_fact.Protocol(data)
        convo_protocol = convo_fact.ConvoProtocol(protocol)
        cg = calc_graph.CG()
        cg.root = convo_protocol

        # pp.pprint(cg.root.to_dict())
        cg.root.update_facts([cg.root.entities['bloating']])
        # pp.pprint(cg.root.to_dict())
        cg.root.update_facts([cg.root.entities['stomachache']])
        # pp.pprint(cg.root.to_dict())
        (val, txt) = cg.step()
        self.assertTrue('indisgestion' in txt)

    def test_indisgestion(self):
        data = json.load(open('lib/tests/test.json'))
        protocol = convo_fact.Protocol(data)
        convo_protocol = convo_fact.ConvoProtocol(protocol)
        cg = calc_graph.CG()
        cg.root = convo_protocol
        print cg.step()
        print cg.step('Yes, I have bloating')
        val, txt = cg.step('Yes, I have stomachache')
        print txt
        self.assertTrue('You have indisgestion' in txt)

    def test_flu(self):
        data = json.load(open('lib/tests/test.json'))
        protocol = convo_fact.Protocol(data)
        convo_protocol = convo_fact.ConvoProtocol(protocol)
        cg = calc_graph.CG()
        cg.root = convo_protocol
        print cg.step()
        print cg.step('No, I do not have bloating')
        pp.pprint(cg.root.to_dict())
        print cg.step('I have a headache')
        val, txt = cg.step('I have high temperature')
        self.assertTrue("flu" in txt)


if __name__ == '__main__':
    unittest.main()