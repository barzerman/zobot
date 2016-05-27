# pylint: disable=empty-docstring, invalid-name, missing-docstring
from lib.barzer import barzer_objects
import config

class NodeValueType(object):
    def __init__(self, name=None, **kwargs):  # pylint: disable=unused-argument
        if name:
            self.type = barzer_objects.BeadFactory.get_type_by_name(name)

    def match_value(self, bead):
        """ returns a tuple:
            {is bead relevant, what's beads interpreted value}
        """
        if self.type == type(bead):
            return True, bead
        else:
            return False, None

class NodeValueTypeBool(NodeValueType):
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
    # TODO:
    # create a correct value type object by name
    return NodeValueType
