import json

class Fact:

    def __init__(self, name, entity=None, question=None):
        self.name = name
        self.entity = entity
        self.question = question


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
            f = Fact(fact_name, fact['entity'], fact['question'])
            self.facts[fact_name] = f


        for (outcome_name, outcome) in data['outcomes'].values():
            o = Outcome([self.facts[f] for f in outcome['facts']])
            self.outcomes[outcome_name] = o



class BoolValue(CGNodeValue):
    pass


class AndOperator(CGOperator):
    op_name = 'AND'

    def calc(self, children=None, input_val=None):
        output_value = CGNodeValue()
        if children:
            for c in children:
                if c.is_set():
                    if c.value == False:
                        output_value.set_val(False)
                        return output_value
                else:
                    return output_value

        output_value.set_val(True)
        return output_value


class OrOperanor(CGOperator):
    op_name = 'OR'

    def calc(self, children=None, input_val=None):
        output_value = CGNodeValue()
        not_cnt = 0

        if children:
            for c in children:
                if c.is_set():
                    if c.value == True:
                        output_value.set_val(True)
                        return output_value
                    else:
                        not_cnt += 1

        if not_cnt == len(self.children):
            output_value.set_val(False)

        return output_value


class ConvoFact(CGNode):

    def __init__(self, fact):
        super(ConvoFact, self).__init__(value=BoolValue())
        self.name = fact.name
        self.question = fact.question
        self.entities = fact.entities

    def step(self, input_val):
        return self.question.text


class ConvoOutcome(CGNode):

    def __init__(self, outcome):
        super(ConvoOutcome, self).__init__(value=BoolValue(), op=AndOperator)
        self.name = outcome.name
        self.set_children([ConvoFact(f) for f in outcome.facts])


    def score(self):
        if self.value.is_set():
            if self.value == True:
                return 1
            else:
                return 0
        else:
            cnt = 0.0
            for fact in self.children:
                if fact.is_set():
                    cnt += 1
            return cnt / len(self.children)


class ConvoProtocol(CGNode):

    def __init__(self, protocol):
        super(ConvoProtocol, self).__init__(value=BoolValue())
        self.set_children([ConvoOutcome(o) for o in protocol.outcomes])

        def current_child(self):
            return sorted([(outcome.score(), outcome) for outcome in self.children])[-1][1]


