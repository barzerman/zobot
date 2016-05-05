# pylint: disable=empty-docstring
""" simple entity based fact node implementation """
from lib import calc_graph
from lib import barzer

class CGEntityNode(calc_graph.CGNode):
    """ """
    def __init__(self, ent, expression=None):
        """
        Arguments:
            ent (barzer.Entity)
            expression (arithmetic expression over value)
        """
        self.ent = ent
        # when this gets filled step will complete
        self.ent_val = None
        self.expression = expression

    def step(self, input_val=None):
        """ """
        # Processing steps
        # 1. parse input_val using Barzer
        # 2. try to fill self.ent
        # 3. try to calculate / fill value
        # 4. return step response (BOT reply, completion status)
