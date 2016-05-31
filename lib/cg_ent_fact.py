# pylint: disable=empty-docstring, invalid-name, missing-docstring
""" simple entity based fact node implementation """
import json
import sys

from functools import partial
from lib.barzer import barzer_objects
from lib import calc_graph, calc_node_value_type
from lib import barzer


class CompareExpression(object):
    """ arithmetic entity value expression """
    router = {
        '=': lambda values, x: x == values,
        '<': lambda values, x: x < values,
        '>': lambda values, x: x > values,
        '<=': lambda values, x: x <= values,
        '>=': lambda values, x: x >= values,
        '!=': lambda values, x: x != values,
        'in': lambda values, x: any(x == _ for _ in values),
        'out': lambda values, x: not any(x == _ for _ in values),
        '<>': lambda values, x: x >= values[0] and x <= values[1],
        '><': lambda values, x: x < values[0] or x > values[1],
    }

    def __call__(self, x):
        val = x
        if isinstance(x, (list, tuple)):
            for v in x:
                if v is not None:
                    val = v
                    break
        return self.func(val)

    def __init__(self, data):
        self.func = partial(
            self.router[data.get('op', '=')], data.get('values'))


class CGEntityNode(calc_graph.CGNode):
    """ """
    node_type_id = 'entity'

    def __init__(
            self, data, expression=None,
            ent_question=None, barzer_svc=None
        ):
        """
        Arguments:
            ent (barzer.Entity|dict) - dict is passed to the Entity
                constructor
            expression (arithmetic expression over value)
        """
        super(CGEntityNode, self).__init__()
        self.activated = False

        self.ent = data if isinstance(
            data, barzer_objects.Entity) else barzer_objects.Entity(data)

        self.ent_value = None
        self.confidence = 0.5

        self.value_type = None
        if expression:
            self.expression = expression
        elif isinstance(data, dict):
            self.value_type = calc_node_value_type.make_value_type(
                data.get('value_type'))
            expression = data.get('expression')
            self.expression = CompareExpression(
                expression) if expression else None
        else:
            self.expression = None

        if not self.value_type:
            self.value_type = calc_node_value_type.NodeValueTypeNumber()

        self.ent_question = ent_question
        self.barzer_svc = barzer_svc or barzer.barzer_svc.barzer
        self.active_value_type = self.value_type
        self.special_response = None

    def as_dict(self):
        result = {
            'type': self.node_type_id,
        }
        for attr in self.__dict__:
            if getattr(self, attr, None) is not None:
                result[attr] = str(getattr(self, attr))
        return result

    def is_activated(self):
        return self.activated

    def deactivate(self):
        self.activated = False
        self.active_value_type = self.value_type

    def activate(self, value_type=None):
        if not self.activated:
            self.activated = True
        self.active_value_type = value_type or self.value_type

    def is_ent_val_ready(self):
        """ True if we have entity value with high confidence """
        return self.ent_value and self.confidence > 0.5

    def get_bot_response(self, beads=None):
        if self.special_response:
            return self.special_response
        else:
            return self.get_pure_question(beads)

    def get_pure_question(self, beads=None):
        """ based on the value of `beads` as well as the current node state
        produces the bot response phrase
        Ags:
            beads list(lib.barzer.barzer_objects.Bead) - result of the
            user input parse
        Returns:
            text
        """
        if self.value.is_set():
            return 'I understand'

        if self.ent_question:
            basic_question = self.ent_question
        else:
            if self.expression:
                basic_question = 'What is your ' + self.ent.name + '?'
            else:
                basic_question = 'Do you have a ' + self.ent.name + '?'

        if beads:
            return 'Sorry I didn\'t get that. ' + basic_question
        else:
            return basic_question

    def compute_expression(self):
        """ once ent_val is ready call this to pupulate output value """
        if self.is_ent_val_ready():
            if self.expression:
                self.value.set_val(self.expression(self.ent_value))
            else:
                self.value.set_val(True)
            return True
        else:
            return False

    def set_val_and_compute(self, bead_val):
        self.ent_value = bead_val
        self.confidence = 1.0
        self.deactivate()
        self.special_response = None
        return self.compute_expression()

    def analyze_beads(self, beads):
        """ analyzes beads. if applicable tries to fill value
        Args:
            beads list(Beads)
        Returns:
            bool(if computation could be completed)
        """
        for bead in beads:
            if isinstance(bead, (barzer_objects.EntityBase)):
                if bead.match_ent(self.ent):
                    if not self.expression:
                        self.ent_value, self.confidence = True, 1.0
                        return self.compute_expression()
                    else:
                        is_match, bead_val = self.active_value_type.match_value(bead)
                        if is_match:
                            return self.set_val_and_compute(bead_val)
                        else:
                            self.set_special_response(bead_val)

        if self.is_activated() and self.active_value_type:
            # if nothing matched explicitly and node is activated
            prospect_values = list()
            for bead in beads:
                is_match, bead_val = self.active_value_type.match_value(bead)
                if is_match:
                    return self.set_val_and_compute(bead_val)
                else:
                    prospect_values.append(bead_val)

            self.set_special_response(prospect_values)

        if not self.is_activated():
            self.activate()

        return False

    def set_special_response(self, bead_val):
        if bead_val is not None:
            if isinstance(bead_val, list) and len(bead_val) > 1:
                self.special_response = 'None of these values seem valid {}. {}'.format(
                    ','.join(str(x) for x in bead_val),
                    self.get_pure_question())
            else:
                self.special_response = '{} is not valid. {}'.format(
                    bead_val[0] if isinstance(bead_val, list) else bead_val,
                    self.get_pure_question())

    def step(self, input_val=None):
        """ """
        self.special_response = None
        if self.is_set():
            return None
        elif self.compute_expression():
            # here if were able to compute entity expressions
            return None
        else:
            if input_val:
                beads = barzer_objects.BeadFactory.make_beads_from_barz(
                    self.barzer_svc.get_json(input_val))
                calc_completed = self.analyze_beads(beads)
                return calc_graph.CGStepResponse(
                    text=self.get_bot_response(beads),
                    beads=beads,
                    step_occured=calc_completed
                )
            else:
                self.activate()
                return calc_graph.CGStepResponse(
                    text=self.get_bot_response()
                )
