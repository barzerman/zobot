# pylint: disable=line-too-long, missing-docstring, invalid-name, superfluous-parens
""" core calc graph objects """
import sys

class NodeValueNotSet(Exception):
    """ attempt to get the not set value"""

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

    def as_dict(self):
        return {'value_type': self.val_type, 'is_array': self.is_array, 'value': self.value}

    def __str__(self):
        if self.is_set():
            return str(self.value)
        else:
            return '<VALUE NOT SET>'

    def unset(self):
        """ unset value """
        if hasattr(self, 'val_'):
            delattr(self, 'val_')

    def is_true(self):
        return self.is_set() and self.val_ is True

    def is_false(self):
        return self.is_set() and self.val_ is False

    def is_set(self):
        """ when true it's safe to get value by calling `value`"""
        return hasattr(self, 'val_')

    def set_val(self, val):
        """ set value """
        if not self.is_array and isinstance(val, (list, set, frozenset)):
            self.is_array = True
        setattr(self, 'val_', val)
        return self

    def equal(self, another_cg_value):
        if self.is_set() and another_cg_value.is_set():
            return self.val_ == another_cg_value.val_
        else:
            return False

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

    def current(self):  # pylint: disable=missing-docstring
        return self.children[self.pos] if self.pos < len(self.children) else None

    def next(self):  # pylint: disable=missing-docstring
        self.pos += 1
        return self.current()


class CGOperator(object):
    """ default operator is a list """
    op_name = 'LIST'

    @classmethod
    def static_calc(cls, children=None, input_val=None):  # pylint: disable=unused-argument
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
    def init_output_val(cls, val_type, value=None, is_array=False):
        """ initializes `value` as operator's output given number of children """
        return CGNodeValue(
            value=value,
            val_type=val_type,
            is_array=is_array
        )

    @classmethod
    def arg_iterator(cls):
        return CGChildIterator


class CGStepResponse(object):
    """ represents CGNode calculation step response
    may be returned from `CGNode.step`
    """
    def __init__(self, step_occured=False, text=None, beads=None):
        """
        Args:
            text (str) - textual response from the bot for the next step
            beads (list(lib.barzer.barzer_objects.Bead)) - barz response
        """
        self.text = text
        self.beads = beads
        self.step_occured = step_occured

    def __str__(self):
        return 'text={} beads={} step_occured={}'.format(
            self.text,
            self.beads,
            self.step_occured
        )

    def __nonzero__(self):
        return bool(self.step_occured)

class CGNodeMeta(type):
    """ CGNode metaclass
    children of CGNode can later on be located by
    their `node_type_id` field, or, in case it's
    not defined by lower case type name
    """
    def __init__(cls, name, bases, dct):
        if not hasattr(cls, 'node_type_registry'):
            cls.node_type_registry = dict()
        else:
            cls.node_type_registry[
                getattr(cls, 'node_type_id', name.lower())
            ] = cls
        super(CGNodeMeta, cls).__init__(name, bases, dct)

class CGNode(object):
    __metaclass__ = CGNodeMeta
    """ baseclass for the calc graph node """
    def __init__(
            self,
            op=None,
            val_type=None,
            value=None,
            children=None,
            is_array=False
    ):
        """
        Arguments:
            op (CGOperator)
            val_type (CGNodeValueType)
        """
        self.op = op
        self.children = self.value = None
        self.value = CGOperator.init_output_val(
            val_type=val_type,
            value=value,
            is_array=children and len(children) > 1 or is_array
        )
        if children:
            self.set_children(children)

    @classmethod
    def get_class_by_node_type_id(cls, node_type_id):
        if not node_type_id:
            return CGNode
        else:
            return cls.node_type_registry.get(  # pylint: disable=no-member
                node_type_id, CGNode if node_type_id else None
            )

    def as_dict(self):
        result = dict()
        if self.op:
            result['op'] = self.op
        if self.children:
            result['children'] = [c.as_dict() for c in self.children]
        return result

    def set_children(self, children):
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
        if self.op:
            return self.op.calc(children, input_val)
        else:
            return CGOperator.static_calc(children=children, input_val=input_val)

    def step(self, input_val=None):
        """ single calculation step
        tries to calculate next unfinished node
        Returns:
            CGStepResponse
        """
        ret = CGStepResponse()
        if not self.is_set():
            current_child = self.current_child()
            while current_child:
                if current_child.is_set():
                    current_child = self.find_next_unset_child()
                else:
                    ret = current_child.step(input_val=input_val)
                    if not current_child.is_set():
                        return ret
                    else:
                        ret.step_occured = True

            if not current_child:
                self.value = self.op_calc(
                    children=self.get_children(),
                    input_val=input_val
                )

        return ret

class CG(object):
    """ calculation dag """
    def __init__(self, data=None):
        """
        """
        self.nodes = dict()
        self.root = CGNode()
        self.init_from_data(data, self.root)

    def init_from_data(self, data, node, list_node_type=CGNode):
        if isinstance(data, (list, set, frozenset)):
            for d in data:
                return node.set_children(
                    [self.init_from_data(d, list_node_type()) for d in data]
                )
        elif isinstance(data, dict):
            node_type = CGNode.get_class_by_node_type_id(
                data.get('node_type')
            )
            the_id = data.get('id')
            if 'data' in data:
                node_data = data['data']
                n = node_type(node_data)
                if the_id is None:
                    the_id = node_data.get('node_id')
            else:
                val_type = data.get('type')
                op = data.get('op')
                value = data.get('value')
                n = node_type(op, val_type, value)

            if the_id:
                self.nodes[the_id] = n

            children = data.get('children')
            if children:
                return self.init_from_data(children, n)
            else:
                return n

        return node

    def as_dict(self):
        return self.root.as_dict()

    @property
    def value(self):
        return self.root.value

    def step(self, input_val=None):
        step_response = self.root.step(input_val=input_val)
        return self.root.value, step_response
