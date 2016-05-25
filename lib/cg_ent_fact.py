# pylint: disable=empty-docstring, invalid-name, missing-docstring
""" simple entity based fact node implementation """
from functools import partial
from lib.barzer import barzer_objects
from lib import calc_graph
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

    def __init__(self, data, expression=None, ent_question=None, barzer_svc=None):
        """
        Arguments:
            ent (barzer.Entity|dict) - dict is passed to the Entity
                constructor
            expression (arithmetic expression over value)
        """
        super(CGEntityNode, self).__init__()
        entity_type = barzer_objects.Entity
        self.ent = data if isinstance(data, entity_type) else entity_type(data)
        # TODO: add negative entity here - mathcing a negative entity should
        #       be interpreted as value False
        # when this gets filled step will complete
        self.ent_value = None  # TODO: refactor
        self.confidence = 0.5
        self.waiting_for_value = False
        self.question_count = 0

        if expression:
            self.expression = expression
        elif isinstance(data, dict) and 'expression' in data:
            self.expression = CompareExpression(data['expression'])
        else:
            self.expression = None

        self.ent_question = ent_question
        self.barzer_svc = barzer_svc or barzer.barzer_svc.barzer

    def is_ent_val_ready(self):
        """ True if we have entity value with high confidence """
        return self.ent_value and self.confidence > 0.5

    def get_question(self, beads=None):
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

        # TODO: hook up a more advanced question generation here
        #  1. randomized "Sorry I didn't get it"
        #  2. automated and randomized entity question generation based on both
        #     entity and expression
        if self.ent_question:
            basic_question = self.ent_question
        else:
            if self.expression:
                basic_question = 'What is your ' + self.ent.name + '?'
            else:
                basic_question = 'Do you have a ' + self.ent.name + '?'

        if self.question_count > 0:
            return 'Sorry I didn\'t get that. ' + basic_question
        else:
            self.question_count += 1
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

    def analyze_beads(self, beads):
        """ analyzes beads. if applicable tries to fill value
        Args:
            beads list(Beads)
        Returns:
            bool(if computation could be completed)
        """
        for bead in beads:
            if self.expression:
                if self.waiting_for_value:
                    if isinstance(bead, barzer_objects.Number):
                        self.ent_value = bead.value
                        self.confidence = 1.0
                        self.waiting_for_value = False
                    elif isinstance(bead, barzer_objects.Range):
                        self.ent_value = bead.get_as_type_pair()
                        self.confidence = 1.0
                        self.waiting_for_value = False
                else:
                    if isinstance(bead, (barzer_objects.EntityBase)):
                        if bead.match_ent(self.ent):
                            # TODO: match negative entity here if possible
                            if isinstance(bead, barzer_objects.ERC):
                                self.ent_value = bead.range.get_as_type_pair()
                                self.confidence = 1.0
                            elif isinstance(bead, barzer_objects.EVR):
                                self.ent_value = [x for x in bead.iterate_type((
                                    barzer_objects.Range,
                                    barzer_objects.Number))]
                                self.confidence = 1.0
                            else:
                                self.waiting_for_value = True
            else:
                if isinstance(bead, barzer_objects.EntityBase):
                    if bead.match_ent(self.ent):
                        self.ent_value = True
                        self.confidence = 1.0
                else:
                    if 'yes' in str(bead).lower():
                        self.ent_value = True
                        self.confidence = 1.0
                    elif 'no' in str(bead).lower():
                        self.ent_value = False
                        self.confidence = 1.0

        return self.compute_expression()

    def step(self, input_val=None):
        """ """
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
                    text=self.get_question(beads),
                    beads=beads,
                    step_occured=calc_completed
                )
            else:
                return calc_graph.CGStepResponse(
                    text=self.get_question()
                )
