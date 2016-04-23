import unittest
import sys
from lib import calc_graph

class CalcGraphTestCase(unittest.TestCase):
    def test_basic(self):
        cg = calc_graph.CG()

if __name__ == '__main__':
    unittest.main()
