# pylint: disable=empty-docstring, invalid-name, missing-docstring
import sys
import config
from lib.barzer import barzer_objects

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

    def default_question_prefix(self):
        return None

class NodeValueTypeNumber(NodeValueType):
    node_value_type = 'number'
    def __init__(self, lo=None, hi=None, **kwargs): # pylint: disable=unused-argument
        """ numeric value type.
        Args:
             lo (Number) - optional smallest allowed value
             hi (Number) - optional highest allowed value
        """
        super(NodeValueTypeNumber, self).__init__()
        self.lo, self.hi = lo, hi
        self.type = barzer_objects.Number

    def match_number(self, num):
        if self.lo is not None:
            if num < self.lo:
                return False
        if self.hi is not None:
            if num > self.hi:
                return False

        return True

    def match_value(self, bead):
        if isinstance(bead, barzer_objects.Number):
            if self.match_number(bead.value):
                return True, bead.value
            else:
                return False, bead.value
        if isinstance(bead, barzer_objects.Range) and bead.is_numeric():
            num = bead.get_as_single_number()
            if self.match_number(num):
                return True, num
            else:
                return False, num
        elif isinstance(bead, barzer_objects.ERC):
            num = bead.range.get_as_single_number()
            if self.match_number(num):
                return True, num
            else:
                return False, num
        elif isinstance(bead, barzer_objects.EVR):
            for x, the_type in bead.iterate_type(
                    (barzer_objects.Range, barzer_objects.Number)):
                if the_type == barzer_objects.Range:
                    num = bead.get_as_single_number()
                else:
                    num = x.value
            if self.match_number(num):
                return True, num
            else:
                return False, num
        else:
            return False, None

    def default_question_prefix(self):
        return 'What is your'

class NodeValueTypeYesNo(NodeValueType):
    node_value_type = 'bool'
    def __init__(self, **kwargs): # pylint: disable=unused-argument
        """
        Yes/No value type
        """
        super(NodeValueTypeYesNo, self).__init__()
        self.true_val = barzer_objects.Entity(config.RulesSettings.YES_ENTITY)
        self.false_val = barzer_objects.Entity(config.RulesSettings.NO_ENTITY)

    def match_value(self, bead):
        if isinstance(bead, barzer_objects.EntityBase):
            if bead.match_ent(self.true_val):
                return True, True
            elif bead.match_ent(self.false_val):
                return True, False

        # this is not a yesno value
        return False, None

    def default_question_prefix(self):
        return 'Do you have'

def make_value_type(value_type_data):
    """ creates a value type object from value_type_data
    Args:
        value_type_data (str|dict) - when str it's simply a type name
            when dict then the type name is in `type` attribute
    """
    if not value_type_data:
        return None
    args = {}
    if isinstance(value_type_data, str):
        type_name = value_type_data
    elif isinstance(value_type_data, dict):
        type_name = value_type_data['type']
        args = {k: v for k, v in value_type_data.iteritems() if k != 'type'}

    the_type = NodeValueType.node_val_type_registry.get(type_name) # pylint: disable=no-member
    return the_type(**args) if the_type else None
