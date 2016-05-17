# pylint: disable=missing-docstring,unused-import,invalid-name,no-self-use
import unittest
import sys
from lib import calc_graph
from lib import cg_ent_fact
from lib.barzer.barzer_svc import barzer
from lib.barzer import barzer_objects


class CalcGraphTestCase(unittest.TestCase):
    CG_DATA = [
        {'value': '1234'}
    ]

    def test_basic(self):
        cg = calc_graph.CG(self.CG_DATA)
        n = calc_graph.CGNode()
        self.assertFalse(cg.value.is_set())
        cgdict = cg.root.to_dict()
        self.assertEquals(len(cgdict['children']), len(self.CG_DATA))
        # computational step
        val, response = cg.step()
        self.assertTrue(cg.value.value)


class CgEntFact(unittest.TestCase):
    def test_cg_ent_node_basic(self):
        objbarz = barzer_objects.BeadFactory.make_beads_from_barz(
            barzer.get_json('headache'))
        print >> sys.stderr, "DEBUG >>>", objbarz, "<<<"
        node = cg_ent_fact.CGEntityNode(
            barzer_objects.Entity(
                {
                    'class': 459,
                    'subclass': 3,
                    'id': 'HEADACHE',
                    'name': 'Headache'
                }))

        node.step()


if __name__ == '__main__':
    unittest.main()
