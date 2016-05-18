# pylint: disable=missing-docstring, invalid-name, trailing-whitespace, line-too-long
from collections import defaultdict, deque
import pqdict
from lib import calc_graph
from toposort import toposort


class Fact(object):
    def __init__(self, data):
        self.id = data['id']
        self.entities = data['entities']
        self.question = data['question']


class Entity(object):
    def __init__(self, _id):
        self.id = _id


class CompositeFact(object):
    def __init__(self, protocol, data):
        self.id = data['id']
        self.operator = data['operator']
        self.facts = [protocol.facts[fact_id] for fact_id in data['facts'] if fact_id in protocol.facts]


class Protocol(object):
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

        for facts_of_equal_priority in toposort(G):
            for _id in facts_of_equal_priority:
                if _id not in self.facts:
                    self.facts[_id] = CompositeFact(self, composite_facts[_id])

        self.terminals = [self.facts[t] for t in data['terminals']]


class ProbaValue(calc_graph.CGNodeValue):
    def __init__(self, value=None, val_type=None, is_array=False):
        super(ProbaValue, self).__init__(value, val_type, is_array)
        self.proba_val = 0.5

    def to_dict(self):
        return self.proba_val

    def set_proba(self, p):
        self.proba_val = p
        if p == 1:
            self.set_val(True)
        elif p == 0:
            self.set_val(False)

    def proba(self):
        return self.proba_val

    def is_true(self):
        return self.is_set() and self.value

    def is_false(self):
        return self.is_set() and not self.value

    def to_f(self):
        return int(bool(self.value)) if self.is_set() else self.proba()


class AndOperator(calc_graph.CGOperator):
    op_name = 'AND'

    def calc(self, children=None, input_val=None):
        output_value = ProbaValue()
        output_value.set_proba(reduce(lambda x, y: x * y, [c.value.proba() for c in children]))
        return output_value


class OrOperator(calc_graph.CGOperator):
    op_name = 'OR'

    def calc(self, children=None, input_val=None):
        output_value = ProbaValue()
        output_value.set_proba(max([c.value.proba() for c in children]))
        return output_value


class ConvoFact(calc_graph.CGNode):

    def __init__(self, protocol, fact, parents=None):
        super(ConvoFact, self).__init__()
        self.value = ProbaValue()
        self.id = fact.id
        self.question = fact.question
        self.parents = set(parents or [])

        for ent in fact.entities:
            protocol.entity_fact_index[ent].add(self)

    def step(self, input_val=None):
        return self.question

    def remove_parent(self, _id):
        if _id in self.parents:
            self.parents.remove(_id)

    def add_parent(self, p):
        self.parents.add(p)

    def update(self, entity, proba=1):
        self.value.set_proba(proba)  # TODO
        for parent in self.parents:
            parent.pq[self] = self.score()

    def score(self):
        if self.value.is_set():
            return 0
        else:
            return len(self.parents)

    def to_dict(self):
        data = {'id': self.id, 'value': self.value.to_dict()}
        if self.children:
            data['children'] = [c.to_dict() for c in self.children]
        return data


class ConvoCompositeFact(calc_graph.CGNode):
    OPERATOR_MAP = {
        'AND': AndOperator,
        'OR': OrOperator,
    }

    def __init__(self, protocol, fact, parents=None, terminal=False):
        op = self.OPERATOR_MAP.get(fact.operator)
        super(ConvoCompositeFact, self).__init__(
            op=op() if op else None
        )

        self.parents = set(parents or [])
        self.terminal = terminal
        self.pq = pqdict.maxpq()
        self.protocol = protocol

        self.id = fact.id
        self.set_children([
            protocol.create_or_update_fact(
                protocol, f, [self]) for f in fact.facts])

        self.value = self.op.calc(children=self.get_children())

    def set_children(self, children):
        self._nodes = {}
        for ch in children:
            self.pq[ch] = 0
            self._nodes[ch.id] = ch
        super(ConvoCompositeFact, self).set_children(children)

    def to_dict(self):
        data = {'id': self.id, 'op': self.op.op_name, 'value': self.value.to_dict()}
        if self.children:
            data['children'] = [c.to_dict() for c in self.children]
        return data

    def remove_parent(self, _id):
        self.parents.remove(_id)

    def add_parent(self, p):
        self.parents.add(p)

    def current_child(self):
        return self.pq.top()

    def update(self):
        self.value = self.op.calc(children=self.get_children())
        if self.terminal:
            self.protocol.pq[self] = self.score()
        else:
            for parent in self.parents:
                parent.pq[self] = self.score()

        if self.value.is_false():
            for ch in self.children:
                ch.remove_parent(self.id)

    def score(self):
        if self.value.is_set():
            return 0
        else:
            return self.value.proba()


class ConvoProtocol(calc_graph.CGNode):

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
        self.pq = pqdict.maxpq()
        for t in self.terminals.values():
            self.pq[t] = t.score()

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
            entities = self.extract_entities(input_val)  # TODO
            self.update_facts(entities, 'No' in input_val)  # TODO

        resp = self.current_child().step(input_val)

        for _id, t in self.terminals.items():
            print _id, t.value.is_true()
            if t.value.is_true():
                return "You have " + _id

        return resp

    def current_child(self):
        return self.pq.top()
