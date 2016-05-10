import json
from collections import defaultdict, deque
from pqdict import PQDict
from calc_graph import *

class Fact:

    def __init__(self, data):
        self.id = data['id']
        self.entities = data['entities']
        self.question = data['question']


class Entity:

    def __init__(self, _id):
        self.id = _id


class CompositeFact:

    def __init__(self, protocol, data):
        self.id = data['id']
        self.operator = data['operator']
        self.facts = [protocol.facts[fact_id] for fact_id in data['facts']]


class Protocol:

    def __init__(self, data):
        self.entities = {}
        self.facts = {}
        self.questions = {}
        self.terminals = []

        for ent in data['entities']:
            e = Entity(ent)
            self.entities[ent] = e

        for fact in data['facts']:
            f = Fact(fact)
            self.facts[fact['id']] = f

        # topologically sorting composite facts 
        G = defaultdict(set)
        composite_facts = {}
        for composite_fact in data['composite_facts']:
            composite_facts[composite_fact['id']] = composite_fact

            for fact_id in composite_fact['facts']:
                G[fact_id].add(composite_fact['id'])

        sequence = []

        def dfs(v):
            for v1 in G[v]:
                dfs(v1)
            if v not in self.facts:
                sequence.append(v)

        for fact in self.facts.keys():
            dfs(fact)

        for _id in sequence:
            self.facts[_id] = CompositeFact(self, composite_facts[_id])

        self.terminals = [self.facts[t] for t in data['terminals']]



class ProbaValue(CGNodeValue):

    def __init__(self, value=None, val_type=None, is_array=False):
        self.val_type = val_type
        self.is_array = is_array
        self.proba_val = 0.5
        if value is not None:
            self.set_val(value)

    def to_dict(self):
        return self.proba_val

    def set_proba(self, p):
        self.proba_val = p
        if p == 1:
            self.set_val(True)
        if p == 0:
            self.set_val(False)

    def proba(self):
        return self.proba_val

    def is_true(self):
        return self.is_set() and self.val_ == True

    def is_false(self):
        return self.is_set() and self.val_ == False

    def to_f(self):
        if self.is_false():
            return 0
        if self.is_true():
            return 1
        else:
            return self.proba()


class AndOperator(CGOperator):
    op_name = 'AND'

    def calc(self, children=None, input_val=None):
        output_value = ProbaValue()
        output_value.set_proba(reduce(lambda x,y: x*y, [c.value.proba() for c in children]))
        return output_value


class OrOperator(CGOperator):
    op_name = 'OR'

    def calc(self, children=None, input_val=None):
        output_value = ProbaValue()
        output_value.set_proba(max([c.value.proba() for c in children]))
        return output_value


class ConvoFact(CGNode):

    def __init__(self, protocol, fact, parents=None):
        super(ConvoFact, self).__init__()
        self.value = ProbaValue()
        self.id = fact.id
        self.question = fact.question
        self.parents = parents

        for ent in fact.entities:
            protocol.entity_fact_index[ent].add(self)

    def step(self, input_val=None):
        return self.question

    def remove_parent(self, _id):
        self.parents = filter(lambda p: p.id != _id, self.parents)

    def add_parent(self, p):
        self.parrents.append(p)

    def update(self, entity, proba=1):
        self.value.set_proba(proba) # TODO
        for parent in self.parents:
            parent.priorities[self.id] = self.score()

    def score(self):
        if self.value.is_true():
            return 10**5
        else:
            return 10**5-len(self.parents)

    def to_dict(self):
        data = {'id': self.id, 'op': self.op.op_name, 'value': self.value.to_dict()}
        if self.children:
            data['children'] = [c.to_dict() for c in self.children]
        return data


class ConvoCompositeFact(CGNode):

    def __init__(self, protocol, fact, parents=None, terminal=False):
        if fact.operator == "AND":
            operator = AndOperator()
        if fact.operator == "OR":
            operator = OrOperanor()
        self.parents = parents
        self.terminal = terminal
        self.priorities = PQDict()
        self.protocol = protocol
        if not self.parents:
            self.parents = []

        super(ConvoCompositeFact, self).__init__(op=operator)
        self.id = fact.id
        self.set_children([protocol.create_or_update_fact(protocol, f, [self]) for f in fact.facts])
        self.value = self.op.calc(children=self.get_children())
    
    def set_children(self, children):
        self._nodes = {}
        for ch in children:
            self.priorities[ch.id] = 10**5
            self._nodes[ch.id] = ch
        super(ConvoCompositeFact, self).set_children(children)


    def to_dict(self):
        data = {'id': self.id, 'op': self.op.op_name, 'value': self.value.to_dict()}
        if self.children:
            data['children'] = [c.to_dict() for c in self.children]
        return data


    def remove_parent(self, _id):
        self.parents = filter(lambda p: p.id != _id)

    def add_parent(self, p):
        self.parrents.append(p)

    def current_child(self):
        dkey, pkey = self.priorities.peek()
        return self._nodes[dkey]

    def update(self):
        self.value = self.op.calc(children=self.get_children())
        if self.terminal:
            self.protocol.priorities[self.id] = self.score()
        else:
            for parent in self.parents:
                parent.priorities[self.id] = self.score()

        if self.value.is_false():
            for ch in self.children:
                ch.remove_parent(self.id)
    
    def score(self):
        if self.value.is_set():
            return 1
        else:
            return 1-self.value.proba()


class ConvoProtocol(CGNode):

    def __init__(self, protocol):
        super(ConvoProtocol, self).__init__()
        self.value = ProbaValue()
        self.entity_fact_index = defaultdict(set)
        self.terminals = {}
        self.facts_ = {}
        self.entities = protocol.entities

        for t in protocol.terminals:
            self.terminals[t.id] = ConvoCompositeFact(protocol=self, fact=t, terminal=True)

        self.set_children(self.terminals.values())
        self.priorities = PQDict()
        for t in self.terminals.keys():
            self.priorities[t] = self.terminals[t].score()

    def extract_entities(self, input_val=None):
        res = []
        for token in input_val.split():
            if token in self.entities:
                res.append(self.entities[token])
        return res

    def create_or_update_fact(self, protocol, f, parents):
        if f.id in self.facts_:
            self.facts_[f.id].add_parents(parents)
        else:
            if isinstance(f, CompositeFact):
                self.facts_[f.id] = ConvoCompositeFact(protocol, f, parents)
            else:
                self.facts_[f.id] = ConvoFact(protocol, f, parents)

        return self.facts_[f.id]


    def update_facts(self, entities, no=False):
        visited = set()
        to_update = deque()
        print [e.id for e in entities]

        if no:
            proba = 0
        else:
            proba = 1

        for ent in entities:
            for fact in self.entity_fact_index[ent.id]:
                fact.update(ent, proba)
                for parent in fact.parents:
                    if parent.id not in visited:
                        to_update.append(parent)
                        visited.add(parent.id)

        while len(to_update) > 0:
            fact = to_update.popleft()
            fact.update()
            for parent in fact.parents:
                if parent.id not in visited:
                    to_update.append(parent)
                    visited.add(parent.id)

    def step(self, input_val=None):

        if input_val:
            entities = self.extract_entities(input_val) # TODO
            self.update_facts(entities, 'No' in input_val) # TODO
        
        resp = self.current_child().step(input_val)

        for _id, t in self.terminals.items():
            print _id, t.value.is_true()
            if t.value.is_true():
                return "You have " + _id

        return resp

    def current_child(self):
        dkey, pkey = self.priorities.peek()
        return self.terminals[dkey]

