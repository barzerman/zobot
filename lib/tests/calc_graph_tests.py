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
    ENT_NODE_DATA = {
        'headache': {
            'class': 459,
            'subclass': 3,
            'id': 'HEADACHE',
            'name': 'Headache'
        }
    }
    CG_DATA = [
        {
            'node_type': 'entity',
            'data': {
                'class': 459,
                'subclass': 3,
                'id': 'HEADACHE',
                'name': 'Headache'
            }
        }
    ]
    def setUp(self):
        self.ent_node = cg_ent_fact.CGEntityNode(
            barzer_objects.Entity(
                self.ENT_NODE_DATA['headache']
            ))
        self.cg = calc_graph.CG(self.CG_DATA)

    def test_ent_node_graph(self):
        pass

    def test_cg_ent_node_basic(self):
        """ testing standalone CGEntityNode """
        self.assertFalse(self.ent_node.is_set())
        step_ret = self.ent_node.step('heart ache')
        print >> sys.stderr, "DEBUG >>>", bool(step_ret), "<<<"
        self.assertFalse(self.ent_node.is_set())
        step_ret = self.ent_node.step('i have a headache')
        print >> sys.stderr, "DEBUG >>>", 'step occured={}'.format(bool(step_ret)), "<<<"
        self.assertTrue(self.ent_node.is_set())
        print >> sys.stderr, "DEBUG >>>", self.ent_node.value.value, "<<<"

if __name__ == '__main__':
    unittest.main()
