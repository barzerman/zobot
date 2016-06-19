# pylint: disable=missing-docstring, invalid-name, broad-except, logging-format-interpolation
from __future__ import division, absolute_import
from collections import namedtuple
import logging
from json import JSONEncoder

def _default(self, obj): # pylint: disable=unused-argument
    return getattr(obj.__class__, "to_json", _default.default)(obj)

_default.default = JSONEncoder().default  # Save unmodified default.
JSONEncoder.default = _default # replacement

class EntityId(namedtuple('_EntityId', ('eclass', 'subclass', 'id'))):
    """ barzer entity """

class Bead(object):
    """ bead class  - bead is a single element of structured output """
    type_name = ""

    def __init__(self, data=None):
        if data:
            self.origmarkup, self.src = data.get('origmarkup'), data.get('src')
        else:
            self.origmarkup, self.src = None, None

    def value_str(self):  # pylint: disable=no-self-use
        return '<NONE>'

    def __str__(self):
        return '{}:{}'.format(self.type_name, self.value_str())


class ValueBead(Bead):
    type_name = 'number'

    def __init__(self, data):
        super(ValueBead, self).__init__(data)
        self.value = data.get('value')

    def __repr__(self):
        return self.value_str()

    def value_str(self):
        return str(self.value)


class Token(ValueBead):
    """ regular token """
    type_name = 'token'

    def value_str(self):
        return "{}".format(str(self.value))

class Fluff(Token):
    type_name = 'fluff'


class Punct(Token):
    type_name = 'punct'


class Number(ValueBead):
    type_name = 'number'

class EntityBase(Bead):
    """ parent type for entity based types Entity, ERC, EVR """
    def match_ent(self, ent):
        """ given another entbase object compares the main entity """
        return (
            self.eclass == ent.eclass and  # pylint: disable=no-member
            self.subclass == self.subclass and  # pylint: disable=no-member
            self.id == ent.id)  # pylint: disable=no-member

    @classmethod
    def match_by_template(cls, ent_bead, eclass, subclass, entid):
        """ matches ent_bead against class, subclass, id """
        if not eclass:
            return True
        if eclass != ent_bead.eclass:
            return False
        if not subclass:
            return True
        if subclass != ent_bead.subclass:
            return False

        return not entid or entid == ent_bead.id

class Entity(EntityBase):
    def __init__(self, data=None):
        """
        Arguments:
            data (dict) - dictionary returned from barzer
        """
        super(Entity, self).__init__(data)
        if data:
            self.eclass = data.get('class')
            self.subclass = data.get('subclass')
            self.id = data.get('id')
            self.name = data.get('name')
            self.scope = data.get('scope')
            self.category = data.get('category')
            self.relevance = data.get('rel', 0)
        else:
            self.eclass = self.subclass = self.id = self.name = self.scope = self.category = self.relevance = None # pylint: disable=line-too-long

    def match_template(self, eclass, subclass, entid):
        return self.match_by_template(self, eclass, subclass, entid)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return 'entity:{}.{}.{}'.format(
            self.scope if self.scope else self.eclass,
            self.category if self.category else self.subclass,
            self.id)

    def to_json(self):
        ret = {
            'eclass': self.eclass,
            'subclass': self.subclass,
            'id': self.id
        }
        for x in ('name', 'scope', 'category', 'relevance'):
            if getattr(self, x, None) is not None:
                ret[x] = getattr(self, x)
        return ret

    def ent_id(self):
        return EntityId(self.eclass, self.subclass, self.id)

class Range(Bead):
    type_name = "range"

    def __init__(self, data=None):
        super(Range, self).__init__(data)
        if data:
            self.rangetype = data.get('rangetype', 'real')
            self.order = data.get('order')
            self.lo = data.get('lo')
            self.hi = data.get('hi')
        else:
            self.rangetype = self.order = self.lo = self.hi = None

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '({}, {})'.format(str(self.lo), str(self.hi))

    def get_as_type_pair(self, the_type=float):
        try:
            lo = the_type(self.lo)
        except Exception:
            lo = None

        try:
            hi = the_type(self.lo)
        except Exception:
            hi = None

        if lo is not None and hi is not None:
            return (lo, hi) if lo < hi else (hi, lo)
        else:
            return (lo, hi)

    def is_numeric(self):
        return (isinstance(self.lo, (int, float))
                or isinstance(self.lo, (int, float)))

    def to_json(self):
        return {'order': self.order, 'lo': self.lo, 'hi': self.hi}

    def get_as_single_number(self, num_type=float):
        pair = self.get_as_type_pair(the_type=num_type)
        if pair[0] is None or pair[1] is None:
            return None
        else:
            return (pair[0] + pair[1]) / 2

class EVR(EntityBase):
    """ entity value range """
    type_name = "evr"

    def __init__(self, data=None):
        super(EVR, self).__init__(data)
        if data:
            self.ent = Entity(data['ent'])
            self.values = [
                BeadFactory.make_bead_from_dict(x) for x in data.get('values', [])]
        else:
            self.ent = self.values = None

    def match_template(self, eclass, subclass, entid):
        return self.match_by_template(self.ent, eclass, subclass, entid)

    @property
    def eclass(self):
        return self.ent

    @property
    def subclass(self):
        return self.subclass

    @property
    def id(self):
        return self.id

    def __str__(self):
        return '{}:({} [{}])'.format(
            self.type_name, str(self.ent), ','.join(str(x) for x in self.values))

    def ent_id(self):
        return self.ent.id

    def iterate_type(self, the_type=Number):
        """ yields all values of type the_type.
        NOTE: the_type can also be a tuple
        """
        for v in self.values:
            if isinstance(v, the_type):
                yield v, the_type


class ERC(EntityBase):
    type_name = "erc"
    """ entity range combo """
    def __init__(self, data=None):
        super(ERC, self).__init__(data)
        if data:
            self.ent = Entity(data['ent'])
            self.range = Range(data.get('range'))
        else:
            self.ent = self.range = None

    def __str__(self):
        return '{}:({}{})'.format(self.type_name, str(self.ent), self.range)

    def ent_id(self):
        return self.ent.ent_id()

    def match_template(self, eclass, subclass, entid):
        return self.match_by_template(self.ent, eclass, subclass, entid)

    @property
    def eclass(self):
        return self.ent.eclass

    @property
    def subclass(self):
        return self.ent.subclass

    @property
    def id(self):
        return self.ent.id

    def to_json(self):
        return {
            'ent': self.ent,
            'range': self.range
        }

class Time(ValueBead):
    type_name = "time"
    """ time of day """


class Timestamp(Bead):
    type_name = "timestamp"
    """ """
    def __init__(self, data):
        super(Timestamp, self).__init__(data)
        self.date, self.time = data['date'], data['time']

    def __str__(self):
        return '{}:{} {}'.format(self.type_name, self.date, self.time)


class Date(ValueBead):
    type_name = "date"
    """ """


class BeadFactory(object):
    NAME_TYPE = {
        'token': Token,
        'fluff': Fluff,
        'number': Number,
        'punct': Token,
        'range': Range,
        'date': Date,
        'timestamp': Timestamp,
        'entity': Entity,
        'erc': ERC,
        'evr': EVR,
    }

    @classmethod
    def make_beads_from_barz(cls, barz):
        result = list()
        for x in barz.get('beads'):
            b = cls.make_bead_from_dict(x)
            if b:
                result.append(b)
        return result

    @classmethod
    def get_type_by_name(cls, name):
        return cls.NAME_TYPE.get(name)

    @classmethod
    def make_bead_from_dict(cls, data, default_type=None):
        the_type = data.get('type', default_type)
        if the_type == 'entlist':
            return [Entity(x) for x in data['data']]

        bead_type = cls.NAME_TYPE.get(the_type)
        if bead_type:
            try:
                return bead_type(data)
            except Exception as ex:
                logging.warning('make_bead_from_dict:' + str(ex))
        else:
            logging.warning('make_bead_from_dict {}'.format(the_type))
