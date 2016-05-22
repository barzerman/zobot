# pylint: disable=empty-docstring
""" simple entity based fact node implementation """
from lib.barzer import barzer_objects
from lib import calc_graph
from lib import barzer

class CGEntityNode(calc_graph.CGNode):
    """ """
    node_type_id = 'entity'
    def __init__(self, ent, expression=None, ent_question=None, barzer_svc=None):
        """
        Arguments:
            ent (barzer.Entity|dict) - dict is passed to the Entity
                constructor
            expression (arithmetic expression over value)
        """
        super(CGEntityNode, self).__init__()
        entity_type = barzer_objects.Entity
        self.ent = ent if isinstance(ent, entity_type) else entity_type(ent)
        # TODO: add negative entity here - mathcing a negative entity should
        #       be interpreted as value False
        # when this gets filled step will complete
        self.ent_value = None
        self.confidence = 0

        self.expression = expression
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
            basic_question = self.ent.name + '?'

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
                    # TODO: match negative entity here if possible
                    if not self.expression:
                        self.ent_value, self.confidence = True, 1.0
                    elif isinstance(bead, barzer_objects.ERC):
                        self.ent_value = self.expression(
                            bead.range.get_as_type_pair())
                        self.confidence = 1.0
                    elif isinstance(bead, barzer_objects.EVR):
                        self.ent_value = self.expression(
                            [x for x in bead.iterate_type((
                                barzer_objects.Range,
                                barzer_objects.Number))])
                        self.confidence = 1.0
                    else:
                        continue
                    return self.compute_expression()
        return False

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
