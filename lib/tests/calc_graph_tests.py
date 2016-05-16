# pylint: disable=missing-docstring,unused-import,invalid-name
import unittest
import sys, json
from lib import calc_graph, convo_calc

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

if __name__ == '__main__':
    unittest.main()
