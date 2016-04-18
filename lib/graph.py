from collections import OrderedDict, namedtuple

class CGNodeValueType(object):
    def __init__(self):
        pass

class CGNodeValue(object):
    val_ = 'val_'
    def __init__(self, val_type=None):
        self.val_type = val_type

    def is_set(self):
        return hasattr(self, self.val_)

    def set(self, val):
        setattr(self, self.val_, val)

    @property
    def value(self):
        return getattr(self, self.val_, None)

class CGNode(object):
    def __init__(self, children=None, op=None, val_type=None, value=None):
        """
        Arguments:
            op (CGNodeOperator)
            val_type (CGNodeValueType)
        """
        self.op = op
        self.children = children
        self.value = CGNodeValue(val_type=val_type)

class CG(object):
    """ calculation dag """
    def __init__(self):
        self.children = OrderedDict()
        self.parents = OrderedDict()
        self.nodes = OrderedDict()
