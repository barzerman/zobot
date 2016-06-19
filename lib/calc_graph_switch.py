# pylint: disable=line-too-long,missing-docstring,invalid-name

""" switch operator type """
from __future__ import division, absolute_import
from lib import calc_graph

class SwitchNodeCaseData(object):
    def __init__(self, node, val=None):
        """ single case in a switch or IF operator
        if val is None this is an unconditional operator, otherwise
        `val` is used as the case value and `node` is what the case resolves to
        """
        self.check_val = val
        self.node = node

    def check(self, val):
        return self.check_val and val.equal(self.check_val)

class SwitchNodeCases(object):
    def __init__(self, data):
        if not isinstance(data, (set, list, frozenset)):
            data = [data]
        self.cases = [SwitchNodeCaseData(d.get('node'), d.get('check_val')) for d in data]

    def switch_val(self, val):
        for c in self.cases:
            if c.check(val):
                return c.node

class CGSwitchNode(calc_graph.CGNode):
    """ switch node """
    op_name = 'switch'

    def __init__(self, data, graph=None):
        """ switch(condition) cases: [(case, node), ...] default: node
        """
        super(CGSwitchNode, self).__init__()
        cond_node_data = data.get('condition')
        if not isinstance(cond_node_data, dict):
            raise ValueError(
                'Node of type {} must have `condition` key whose value is a node dictionary.'.format(
                    self.op_name))
        self.cond_node = self.make_node_from_data_dict(cond_node_data)
        self.default_node = self.make_node_from_data_dict(data.get('default'))

        self.case_nodes = SwitchNodeCases(data.make_node_from_data_dict('cases'))

        self.next_node = None

    def find_next_unset_child(self):
        if not self.cond_node.is_set():
            return self.cond_node
        elif self.next_node:
            return self.next_node if not self.next_node.is_set() else None
        else:
            self.next_node = self.case_nodes.switch_val(self.cond_node.value)
            return self.next_node

    def step(self, input_val=None):
        """ single calculation step
        tries to calculate next unfinished node
        Returns:
            CGStepResponse
        """
        ret = calc_graph.CGStepResponse()
        if not self.is_set():
            current_child = self.find_next_unset_child()

            while current_child:
                ret = current_child.step(input_val=input_val)
                if not current_child.is_set():
                    return ret
                else:
                    ret.step_occured = True
                    input_val = None

                current_child = self.find_next_unset_child()

            if not current_child:
                self.value.set_val(current_child.value)

        return ret
