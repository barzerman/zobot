from collections import OrderedDict, namedtuple

class CGNodeValueType(object):
    def __init__(self, node):
        pass

class CGNodeValue(object):
    """ node value """
    val_ = 'val_'
    def __init__(self, val_type=None, is_array=False):
        self.val_type = val_type
        self.is_array = is_array

    def is_set(self):
        return hasattr(self, self.val_)

    def set(self, val):
        if not self.is_array and isinstance(val, (list, set, frozenset)):
            self.is_array = True
        setattr(self, self.val_, val)

    @property
    def value(self):
        return getattr(self, self.val_, None)

class CGOperator(object):
    """ default operator is a list """
    def calc(self, children=None, input_val=None):
        """
        Arguments:
            children iterable(CGNode) - parent nodes, on which results of
                this calculation depend
            input_val (str) - optional string input
        Returns
            output_value (CGNodeValue) - operator output
        """
        output_value = GCNodeValue()
        if children:
            if all(c.is_set() for c in children):
                if len(children) > 1:
                    output_value.set([c.value for c in children])
                else:
                    output_value.set(children[0].value)

        return output_value


    @classmethod
    def init_output_val(cls, val_type, num_children=None):
        """ initializes `value` as operator's output given number of children """
        return CGNodeValue(
            val_type=val_type,
            is_array = num_children and num_children > 0
        )

    @classmethod
    def arg_iterator(cls):
        return iter

class CGNode(object):
    def __init__(self, children=None, op=None, val_type=None, value=None):
        """
        Arguments:
            op (CGOperator)
            val_type (CGNodeValueType)
        """
        self.op = op or CGOperator()
        self.children = children
        if self.children:
            self.value = self.op.init_output_val(val_type=val_type, num_children=len(children))
            self.child_iter = self.op.arg_iterator()(self.children)
        else:
            self.value = self.op.init_output_val(val_type=val_type)
            self.child_iter = None

    def get_children(self):
        return self.children

    def is_set(self):
        return self.value.is_set()

    def next_child(self):
        if self.child_iter:
            return self.child_iter.next()
        else:
            return None

    def step(self, input_val=None):
        """ single calculation step
        tries to calculate next unfinished node
        """

        if not self.is_set():
            next_child = self.next_child()
            if not next_child:
                self.value = self.op.calc(
                    children=self.get_children()
                )
            elif not next_child.is_set():
                next_child.step(input_val=input_val)

        return self.value

class CG(object):
    """ calculation dag """
    def __init__(self, data=None):
        """
        """
        self.children = OrderedDict()
        self.parents = OrderedDict()
        self.root = CGNode()

    def step(self, input_val=None):
        return self.root.step(input_val=input_val)
