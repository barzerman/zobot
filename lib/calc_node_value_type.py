# pylint: disable=empty-docstring, invalid-name, missing-docstring
from lib.barzer import barzer_objects
import config
import json

class NodeValueTypeMeta(type):
    def __init__(cls, name, bases, dct):
        if not hasattr(cls, 'node_val_type_registry'):
            cls.node_val_type_registry = dict()
        else:
            cls.node_val_type_registry[
                getattr(cls, 'node_value_type', name.lower())
            ] = cls
        super(NodeValueTypeMeta, cls).__init__(name, bases, dct)

class NodeValueType(object):
    __metaclass__ = NodeValueTypeMeta
    def __init__(self, name=None, **kwargs):  # pylint: disable=unused-argument
        if name:
            self.type = barzer_objects.BeadFactory.get_type_by_name(name)

    def as_dict(self):
        return {'type': getattr(self, 'type', None)}

    def match_value(self, bead):
        """ returns a tuple:
            {is bead a match, what's beads interpreted value}
        """
        if self.type == type(bead):
            return True, bead
        else:
            return False, None


class NodeValueTypeNumber(NodeValueType):
    node_value_type = 'number'
    def __init__(self, lo=None, hi=None, **kwargs): # pylint: disable=unused-argument
        """ numeric value type.
        Args:
             lo (Number) - optional smallest allowed value
             hi (Number) - optional highest allowed value
        """
        self.lo, self.hi = lo, hi
        self.type = barzer_objects.Number

    def match_value(self, bead):
        if isinstance(bead, barzer_objects.Number):
            return True, bead.value
        if isinstance(bead, barzer_objects.Range) and bead.is_numeric():
            return True, bead.get_as_single_number()
        else:
            return False, None

class NodeValueTypeBool(NodeValueType):
    node_value_type = 'bool'
    def __init__(self, true_bead=None, false_bead=None, **kwargs): # pylint: disable=unused-argument
        # TODO: implement config defaults for true_bead false_bead
        super(NodeValueTypeBool, self).__init__()
        self.true_val = true_bead
        self.false_val = false_bead

    def match_value(self, bead):
        if bead == self.true_val:
            # it's a boolean and it is true
            return True, True
        elif bead == self.false_val:
            # it's a boolean and it is false
            return True, False
        else:
            # this is not a boolean value
            return False, None

def make_value_type(type_name, **kwargs):
    the_type = NodeValueType.node_val_type_registry.get(type_name) # pylint: disable=no-member
    return the_type(**kwargs) if the_type else None
