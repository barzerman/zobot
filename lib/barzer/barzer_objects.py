from __future__ import division, absolute_import
from collections import namedtuple
import unittest
import sys
from lib.barzer.barzer_svc import barzer
import logging

class EntityId(namedtuple('_EntityId', ('eclass', 'subclass', 'id'))):
    """ barzer entity """
# {
# 	type: "entity",
# 	class: 459,
# 	scope: "barzer / pager",
# 	category: "protocol",
# 	subclass: 1,
# 	id: "allergic-reaction",
# 	name: "Allergic Reaction",
# 	rel: 0,
# 	src: "allergic reaction",
# 	origmarkup: "0,8;8,1;9,8"
# }
class Bead(object):
    """ bead class  - bead is a single element of structured output """
    type_name = ""
    def __init__(self, data=None):
        self.origmarkup = None
        self.src = None

    def set_params(self, origmarkup=None, src=None):
        """ sets parameters common for all beads """
        self.origmarkup, self.src = origmarkup, src

class Token(Bead):
    """ regular token """
    type_name = 'token'
    def __init__(self, data):
        self.value = data.get('value', '')

class Fluff(Token):
    type_name = 'fluff'

class Punct(Token):
    type_name = 'punct'

class ValueBead(Bead):
    type_name = 'number'
    def __init__(self, data):
        self.value = data.get(value)

class Number(ValueBead):
    type_name = 'number'

class Entity(Bead):
    def __init__(self, data):
        """
        Arguments:
            data (dict) - dictionary returned from barzer
        """
        self.eclass = data['class']
        self.scope = data['scope']
        self.category = data['protocol']
        self.subclass = data['subclass']
        self.id = data['id']
        self.name = data['name']
        self.relevance = data['rel']

    def ent_id(self):
        return EntityId(self.eclass, self.subclass, self.id)

class Range(Bead):
    type_name = "range"
    def __init__(self, data):
        self.rangetype = data.get('rangetype', 'real')
        self.order = data.get('order')
        self.lo = data.get('lo')
        self.hi = data.get('hi')

class EVR(Bead):
    """ entity value range """
    type_name = "evr"
    def __init__(self, data):
        self.ent = data['ent']
        self.values = [BeadFactory.make_bead(x) for x in data.get('values', [])]

    def ent_id(self):
        return self.ent.ent_id()

class ERC(Bead):
    type_name = "evr"
    """ entity range combo """
    def __init__(self, data):
        self.ent = Entity(data['ent'])
        self.range = Range(data.get('range'))

    def ent_id(self):
        return self.ent.ent_id()

class Time(ValueBead):
    type_name = "time"
    """ time of day """


class Timestamp(Bead):
    type_name = "timestamp"
    """ """
    def __init__(self, data):
        self.date, self.time = data['date'], data['time']

class Date(ValueBead):
    type_name = "date"
    """ """

class BeadFactory(object):
    NAME_TYPE = {
        'token': Token,
        'fluff': Fluff,
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
    def make_bead_from_dict(cls, data):
        the_type = cls.NAME_TYPE['type']
        if the_type:
            bead_type = cls.NAME_TYPE.get(the_type)
            try:
                return bead_type(data) if bead_type else None
            except Exception as ex:
                logging.error('make_bead_from_dict:' + str(ex))
