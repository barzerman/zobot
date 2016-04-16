from config import RulesSettings
import logging
import barzer

class ParsedInput(object):
    def __init__(self, barzer_output):
        self.barzer_output = barzer_output


class Fact(object):
    """ single conversation fact """ 

class ConvoFacts(object):
    """ current facts state for a single convo """
    def get_unknown_facts(self, parsed_input):
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

class ConversationIndex(object):
    """ Global object shared by all convos
    convo environment - has access to all knows current conversations index by
    `convo_id`
    """
    def __init__(self):
        """ """
        self.convo_facts = dict()

    def terminate_convo(self, convo_id):
        self.convo_facts.pop(convo_id)

    def create_convo_facts(self, convo_id):
        """ """
        self.convo_facts[convo_id] = ConvoFacts()
        return self.convo_facts[convo_id]

    def get_convo_facts(self, convo_id):
        # retrieves current fact state for a given convo_id
        return self.convo_facts.get(convo_id)

class ConvoState(object):
    def __init__(self, convo_id, global_index, rules):
        """
        global_index - stores states for all conversations
        """
        self.global_index = global_index
        self.rules = rules
        self.facts = self.global_index.get_convo_facts(convo_id)
        if not self.fact_index:
            self.fact_index = self.global_index.create_convo_facts(convo_id)

        self.terminal_facts = []

    def parse_input(self, user_input):
        """ """
        return ParsedInput(barzer.parse(user_input))

    def interpret_input(self, parsed_input, facts):
        new_terminals = []
        for fact in facts:
            fact.apply(parsed_input)
            if fact.is_terminal():
                new_terminals.append(fact)

    def step(self, user_input=None):
        parsed_input = self.parse_input(user_input)
        facts = self.facts.get_unknown_facts(parsed_input)
        new_terminals = self.interpret_input(parsed_input, facts)

        respone = dict()
        if new_terminals:
            self.terminal_facts.extend(new_terminals)
            response['new_terminals'] = new_terminals

        return response
