# pylint: disable=empty-docstring, invalid-name, missing-docstring,too-many-branches
import re
import sys # pylint: disable=unused-import
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
    ALL_BEADS_NOT_MATCHED = (False, None, False)
    ALL_BEADS_NOT_INELIGIBLE = (False, None, True)

    def __init__(self, name=None, **kwargs):  # pylint: disable=unused-argument
        if name:
            self.type = barzer_objects.BeadFactory.get_type_by_name(name)

    def as_dict(self):
        return {'type': getattr(self, 'type', None)}

    def match_all_beads(self, beads): # pylint: disable=no-self-use, unused-argument
        """ for some types and in some cases it's possible to match
        given a list of beads
        Returns:
            tuple:
                matched (boolean) - whether match occured
                matched_value (bead) - imnterpreted matched value
                single_eligible (bool) - whether individual beads should be matched
        """
        return self.ALL_BEADS_NOT_INELIGIBLE

    def match_value(self, bead):
        """ returns a tuple:
            {is bead a match, what's beads interpreted value}
        """
        if self.type == type(bead):
            return True, bead
        else:
            return False, None

    def default_question_prefix(self): #pylint: disable=no-self-use
        return 'What is your'

class NodeValueTypeString(NodeValueType):
    node_value_type = 'string'
    DEFAULT_MAX_BEADS = 128
    DEFAULT_OTHER_TYPES = (
        barzer_objects.Fluff,
        barzer_objects.Number,
        barzer_objects.Punct)
    DEFAULT_MIN_LEN = 1
    DEFAULT_MAX_LEN = 64

    def __init__(
            self,
            max_beads=None,
            other_types=None,
            pattern=None,
            concat=True,
            min_len=None,
            max_len=None,
            **kwargs
    ): # pylint: disable=unused-argument
        """ numeric value type.
        Args:
             max_beads (Number) - max number of beads to match
             other_types (list()) - optional list of non Token types to treat as tokens
             pattern (regex string) - optional regex to use on the resulting string
             concat (boolean) when true consecutive tokens will be concatenated
        """
        super(NodeValueTypeString, self).__init__()
        self.concat = concat
        self.max_beads = max_beads or self.DEFAULT_MAX_BEADS
        self.min_len = min_len or self.DEFAULT_MIN_LEN
        self.max_len = max_len or self.DEFAULT_MAX_LEN
        self.pattern = re.compile(pattern) if pattern else None

    def _yield_candidate_strings(self, beads):
        lo, hi = 0, 0
        for hi, b in enumerate(beads):
            if (isinstance(b, barzer_objects.Token) or
                    any(isinstance(b, self.DEFAULT_OTHER_TYPES))):
                if not self.concat:
                    yield [b]
            else:
                if hi > lo:
                    yield beads[lo:hi]
                lo = hi
        if hi >= lo:
            yield beads[lo:hi+1]

    def concat_beads(self, beads): #pylint: disable=no-self-use
        if len(beads) == 1:
            return beads[0].value_str()
        else:
            return ''.join(
                x if isinstance(
                    x, barzer_objects.Punct) else str(x.value)+' ' for x in beads
            ).strip()

    def validate(self, s):
        """ validates string """
        if self.pattern:
            return self.pattern.match(s)
        else:
            return self.min_len <= len(s) < self.max_len

    def match_all_beads(self, beads):
        """ returns a tuple (see base class) """
        if len(beads) > self.max_beads:
            return self.ALL_BEADS_NOT_MATCHED

        for bs in self._yield_candidate_strings(beads):
            s = self.concat_beads(bs)
            if self.validate(s):
                return (True, s, False)

        return self.ALL_BEADS_NOT_MATCHED

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
        return 'What is the'

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
        return 'Do you have a'

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
