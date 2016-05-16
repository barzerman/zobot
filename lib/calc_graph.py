# pylint: disable=line-too-long, missing-docstring, invalid-name, superfluous-parens
""" core calc graph objects """
class NodeValueNotSet(Exception):
    """ attempt to get the not set value"""

# end of value types

class CGNodeValue(object):
    """ node value """
    def __init__(self, value=None, val_type=None, is_array=False):
        """
        Arguments:
            value (object) - value
            val_type (CGNodeValueType)
            is_array (bool)
        """
        self.val_type = val_type
        self.is_array = is_array
        if value is not None:
            self.set_val(value)

    def unset(self):
        """ unset value """
        if hasattr(self, 'val_'):
            delattr(self, 'val_')

    def is_set(self):
        """ when true it's safe to get value by calling `value`"""
        return hasattr(self, 'val_')

    def set_val(self, val):
        """ set value """
        if not self.is_array and isinstance(val, (list, set, frozenset)):
            self.is_array = True
        setattr(self, 'val_', val)
        return self

    @property
    def value(self):
        """ value if set, exception otherwise """
        try:
            return getattr(self, 'val_')
        except AttributeError:
            NodeValueNotSet()

    def to_dict(self):  # pylint: disable=missing-docstring
        if self.is_set():
            return {
                'value': getattr(self, 'val_')
            }
        else:
            return 'NOT SET'

class CGChildIterator(object):
    """ basic consecutive iterator
    this can be extended to skip over filled values etc
    """
    def __init__(self, children):
        self.children = children
        self.pos = 0

    def current(self): # pylint: disable=missing-docstring
        return self.children[self.pos] if self.pos < len(self.children) else None

    def next(self):  # pylint: disable=missing-docstring
        self.pos += 1
        return self.current()

class CGOperator(object):
    """ default operator is a list """
    op_name = 'LIST'
    @classmethod
    def static_calc(cls, children=None, input_val=None): # pylint: disable=unused-argument
        """
        Arguments:
            children iterable(CGNode) - parent nodes, on which results of
                this calculation depend
            input_val (str) - optional string input
        Returns
            output_value (CGNodeValue) - operator output
        """
        if children:
            if all(c.is_set() for c in children):
                if len(children) > 1:
                    return CGNodeValue().set_val([c.value for c in children]).value
                else:
                    return CGNodeValue().set_val(children[0].value).value

    def calc(self, children=None, input_val=None):  # pylint: disable=no-self-use, unused-argument
        self.static_calc(children=children, input_val=input_val)

    @classmethod
    def init_output_val(cls, val_type, value=None, num_children=None):
        """ initializes `value` as operator's output given number of children """
        return CGNodeValue(
            value=value,
            val_type=val_type,
            is_array=num_children and num_children > 0
        )

    @classmethod
    def arg_iterator(cls):
        return CGChildIterator

class CGStepResponse(object):
    """ represents CGNode calculation step response
    may be returned from `CGNode.step`
    """
    def __init__(self, text, beads):
        self.text = text
        self.beads = beads

class CGNode(object):
    """ baseclass for the calc graph node """
    def __init__(self, op=None, val_type=None, value=None, num_children=None):
        """
        Arguments:
            op (CGOperator)
            val_type (CGNodeValueType)
        """
        self.op = op
        self.children = None
        self.child_iter = None
        self.value = CGOperator.init_output_val(val_type=val_type, value=value, num_children=num_children)

    def set_children(self, children):
        if not children:
            self.children = None
            self.child_iter = None
            return self.children

        self.children = children
        self.child_iter = CGOperator.arg_iterator()(self.children)

        return self.children

    def get_children(self):
        return self.children

    def is_set(self):
        return self.value.is_set()

    def current_child(self):
        if self.child_iter:
            return self.child_iter.current()

    def next_child(self):
        if self.child_iter:
            return self.child_iter.next()
        else:
            return None

    def find_next_unset_child(self):
        while True:
            current_child = self.next_child()
            if current_child:
                if current_child.is_set():
                    current_child = self.next_child()
                else:
                    return current_child
            else:
                return None

    def to_dict(self):
        data = {'op': self.op.op_name if self.op else CGOperator.op_name, 'value': self.value.to_dict()}
        if self.children:
            data['children'] = [c.to_dict() for c in self.children]
        return data

    def op_calc(self, children, input_val):
        return (self.op.calc(children, input_val)
                if self.op else CGOperator.static_calc(
                    children=children, input_val=input_val))

    def step(self, input_val=None):
        """ single calculation step
        tries to calculate next unfinished node
        Returns:
            CGStepResponse or None if no step occured
        """
        if not self.is_set():
            current_child = self.current_child()
            while current_child:
                if current_child.is_set():
                    current_child = self.find_next_unset_child()
                else:
                    ret = current_child.step(input_val=input_val)
                    if not current_child.is_set():
                        return ret

            if not current_child:
                self.value = self.op_calc(
                    children=self.get_children(),
                    input_val=input_val
                )

class CG(object):
    """ calculation dag """
    def __init__(self, data=None):
        """
        """
        self.nodes = dict()
        self.root = CGNode()
        self.init_from_data(data, self.root)

    def init_from_data(self, data, node):
        if isinstance(data, (list, set, frozenset)):
            for d in data:
                return node.set_children([self.init_from_data(d, CGNode()) for d in data])
        elif isinstance(data, dict):
            the_id = data.get('id')
            val_type = data.get('type')
            op = data.get('op')
            value = data.get('value')

            n = CGNode(op, val_type, value)
            if the_id is not None:
                self.nodes[the_id] = n

            children = data.get('children')
            if children:
                return self.init_from_data(children, n)
            else:
                return n

        return node

    @property
    def value(self):
        return self.root.value

    def step(self, input_val=None):
        step_response = self.root.step(input_val=input_val)
        return self.root.value, step_response
