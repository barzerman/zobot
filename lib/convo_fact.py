import json

class Fact:

    def __init__(self, name, entities=None, conditions=None):
        self.name = name
        self.entities = entities
        self.conditions = conditions


class Entity:

    def __init__(self, name):
        self.name = name
        self.facts = ()


class Outcome:

    def __init__(self, name, facts):
        self.name = name
        self.facts = facts


class Question:

    def __init__(self, text):
        self.text = None


class Protocol:

    def __init__(self, data):
        self.entities = {}
        self.facts = {}
        self.outcomes = {}
        self.questions = {}

        for ent in data['entities']:
            e = Entity(ent)
            self.entities[ent] = e

        for (fact_name, fact) in data['facts'].items():
            f = Fact(fact['entities'])
            self.facts[fact_name] = f


        for (outcome_name, outcome) in data['outcomes'].values():
            o = Outcome([self.facts[f] for f in outcome['facts']])
            self.outcomes[outcome_name] = o



class BoolValue(CGNodeValue):
    pass


class ConvoFact(CGNode):

    def __init__(self, fact):
        super(ConvoFact, self).__init__(value=BoolValue())
        self.name = fact.name
        self.entities = fact.entities


class ConvoOutcome(CGNode):

    def __init__(self, outcome):
        super(ConvoOutcome, self).__init__(value=BoolValue())
        self.name = outcome.name
        self.set_children([ConvoFact(f) for f in outcome.facts])


    def score(self):
        if self.value.is_set():
            if self.value == True:
                return 1
            else:
                return 0


class ConvoProtocol(CGNode):

    def __init__(self, protocol):
        super(ConvoProtocol, self).__init__(value=BoolValue())
        self.set_children([ConvoOutcome(o) for o in protocol.outcomes])
        self.entities = protocol.entities
        self.


    def step(self, input_val=None):
        entities = self.get_entities(input_val)
        for ent in entities:
            for fact in self.fact_index[ent]:
                fact.value.set_val(ent.value)
                if 


