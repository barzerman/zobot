import logging
from config import RulesSettings
import barzer


class ParsedInput(object):
    def __init__(self, barzer_output):
        self.barzer_output = barzer_output


class Fact(object):
    """ single conversation fact """
    def __init__(self):
        self.is_established = False

    def get_next_bot_phrase(self):
        """ given current state of the fact return
        the next question
        """
        logging.error('Unimplemented')
        return ""


class ConvoFacts(object):
    """ current facts state for a single convo """
    def __init__(self, rules):
        """ creates an empty ConvoFacts impression based on the rules """ 
        # TODO: parse rules

    def get_unknown_fact(self, entities_input):
        """ returns next facts that need to be established """
        logging.error('Unimplemented')
        return Fact()


class ConvoRules(object):
    """ Global object: user defined rules - shared by all convos """
    def __init__(self):
        self.rules = self.parse_rules()

    def parse_rules_file(self, fn):
        logging.error('Unimplemented')

    def parse_rules(self):
        """ rules - definitions and relationships between facts and entities  """
        for fn in RulesSettings.RULES_FILES:
            self.parse_rules_file(fn)


class CurrentFactContext(object):
    """ context for the fact currently being established """
    def __init__(self, convo_state, fact=None):
        self.convo_state = convo_state
        self.fact = fact
        self.entities = list()  # entities so far discovered during this establishing

    def established(self):
        return self.fact.is_established

    def interpret_entities(self, entities_input):
        # TODO: implement
        pass

    def get_next_bot_phrase(self):
        self.fact.get_next_bot_phrase()

    def set_fact(self, fact):
        self.fact, self.entities = fact, []


class ConvoStepResponse(object):
    """ ConvoStage.step() returns these objects """
    def __init__(self, text=None, established_fact=None, continues=True):
        self.text = text
        self.continues = state
        self.established_fact = established_fact


class ConvoStage(object):
    def __init__(self, facts):
        """
        convo_id (int) conversation id
        facts (ConvoFacts) - conversation facts for the given stage of the conversation
        """
        self.facts = facts
        self.terminal_facts = []
        self.fact_context = CurrentFactContext()  # fact currently being established
        self.is_over = False

    def parse_input(self, user_input):
        """ """
        return ParsedInput(barzer.parse(user_input))

    def interpret_input(self, entities_input, facts):
        new_terminals = []
        for fact in facts:
            fact.apply(entities_input)
            if fact.is_terminal():
                new_terminals.append(fact)

    def set_fact_context(self):
        unknown_fact = self.facts.get_unknown_fact()
        if unknown_fact:
            self.fact_context.set_fact(unknown_fact)

        return self.fact_context.fact

    def step(self, user_input=None):
        if not self.fact_context.fact and not self.set_fact_context():
            self.is_over = True
            return ConvoStepResponse(continues=False)

        entities_input = self.parse_input(user_input)
        self.fact_context.interpret_entities(entities_input)

        response = ConvoStepResponse()

        if self.fact_context.established():
            self.facts.accept_new_fact(self.fact_context.fact)
            response.established_fact = self.fact_context.fact
            response.continues = bool(self.set_fact_context())
        else:
            response.text = self.fact_context.get_next_bot_phrase()

        if not response.continues:
            self.is_over = True

        return response

class ConvoError(Exception): """ """
class ConvoErrorInvalidId(ConvoError): """ conversation id not found """
class ConvoErrorIsOver(ConvoError): """ conversation is over """


class StagedConvo(object):
    """ staged conversation """
    def __init__(self, rules):
        """ stages is a tree of indeopendent `ConvoStage` objects with simple transition rules
        """
        self.stages = [ConvoStage(self.make_facts(r)) for r in rules]

    def make_facts(self, rules):
        return ConvoFacts()

    def get_next_stage(self):
        logging.error('Not Umplemented')


class ConversationIndex(object):
    """ Global object shared by all convos
    convo environment - has access to all knows current conversations index by
    `convo_id`
    """
    def __init__(self, stage_rules):
        """
        stage_rules - list(StageRules) of rule sets for each stage 
        """
        self.stage_rules = stage_rules
        self.convos = dict()

    def terminate_convo(self, convo_id):
        self.convos.pop(convo_id)

    def create_convo(self, convo_id):
        """ """
        self.convos[convo_id] = StagedConvo(self.terminate_convo)
        return self.convo_facts[convo_id]

    def step(self, convo_id, user_input=None):
        convo = self.convos.get(convo_id)
        if not convo:
            raise ConvoErrorInvalidId()

        state = convo.get_next_stage()
        if not state:
            raise ConvoErrorIsOver()

        return state.step(user_input=user_input)
