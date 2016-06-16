# pylint: disable=missing-docstring,unused-import,invalid-name,no-self-use
import unittest
import sys
import json
from lib import calc_graph
from lib import cg_ent_fact
from lib.barzer.barzer_svc import barzer
from lib.barzer import barzer_objects
from lib import calc_node_value_type

class CalcGraphTestCase(unittest.TestCase):
    CG_DATA = [
        {'node_type': 'basic', 'value': '1234'}
    ]

    def test_basic(self):
        cg = calc_graph.CG(self.CG_DATA)
        calc_graph.CGNode()
        self.assertFalse(cg.value.is_set())
        cgdict = cg.root.to_dict()
        self.assertEquals(len(cgdict['children']), len(self.CG_DATA))
        # computational step
        cg.step()
        self.assertTrue(cg.value.value)


class CgEntFact(unittest.TestCase):
    ENT_NODE_DATA = {
        'headache': {
            'class': 459,
            'subclass': 3,
            'id': 'HEADACHE',
            'name': 'Headache'
        },
        'temperature': {
            'class': 459,
            'subclass': 9,
            'id': 'temperature',
            'name': 'Temperature',
            'expression': {'op': '>', 'values': 200},
            'node_id': 'node.temperature'
        }
    }
    def setUp(self):
        self.ent_node = cg_ent_fact.CGEntityNode(
            barzer_objects.Entity(
                self.ENT_NODE_DATA['headache']
            ))

    def _make_entity_node(self, data):
        if isinstance(data, dict):
            return calc_graph.CG([{'node_type': 'entity', 'data': data}])
        else:
            return calc_graph.CG([{'node_type': 'entity', 'data': x} for x in data])


    def test_value_type(self):
        cg = self._make_entity_node(self.ENT_NODE_DATA['temperature'])
        print >> sys.stderr, "DEBUG test_value_type >>>", json.dumps(cg.as_dict(), indent=4), "<<<"
        val, ret = cg.step()
        print >> sys.stderr, "DEBUG test_value_type after step >>>", val, ret, "<<<"
        temp_val = 100
        val, ret = cg.step(str(temp_val))
        self.assertFalse(val.value)
        self.assertEquals(temp_val, cg.nodes['node.temperature'].ent_value)
        print >> sys.stderr, "DEBUG test_value_type >>>", val.value, ret, cg.nodes['node.temperature'].ent_value, "<<<"

    def test_ent_expressions(self):
        cg = self._make_entity_node(self.ENT_NODE_DATA['temperature'])
        val, ret = cg.step()
        self.assertFalse(val.value)
        self.assertFalse(ret.step_occured)
        val, ret = cg.step('temprerature 99')
        self.assertTrue(ret.step_occured)
        self.assertFalse(val.value)

    def test_ent_node_graph(self):
        cg = calc_graph.CG([
            {
                'node_type': 'entity',
                'data': {
                    'class': 459,
                    'subclass': 3,
                    'id': 'HEADACHE',
                    'name': 'Headache'
                }
            }
        ])
        val, ret = cg.step()
        self.assertFalse(val.value)
        self.assertFalse(ret.step_occured)
        val, ret = cg.step('got headache')
        self.assertTrue(val.value)
        self.assertTrue(ret.step_occured)

    def test_cg_ent_node_basic(self):
        """ testing standalone CGEntityNode """
        self.assertFalse(self.ent_node.is_set())
        step_ret = self.ent_node.step('heart ache')
        print >> sys.stderr, "DEBUG >>>", bool(step_ret), "<<<"
        self.assertFalse(self.ent_node.is_set())
        step_ret = self.ent_node.step('i have a headache')
        print >> sys.stderr, "DEBUG >>>", 'step occured={}'.format(
            bool(step_ret)), "<<<"
        self.assertTrue(self.ent_node.is_set())
        print >> sys.stderr, "DEBUG >>>", self.ent_node.value.value, "<<<"

if __name__ == '__main__':
    unittest.main()
