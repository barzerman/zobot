# pylint: disable=missing-docstring, invalid-name, trailing-whitespace, line-too-long
from collections import defaultdict, deque
import pqdict
from lib import calc_graph
from toposort import toposort
from lib import cg_ent_fact
from lib import barzer_objects
from lib import barzer


class Fact(object):
    def __init__(self, data):
        self.id = data['id']


class EntityFact(Fact):
    def __init__(self, data):
        super(EntityFact, self).__init__(data)
        self.entity = barzer_objects.Entity(data['entity'])
        self.question = data.get('question')
        self.expression = data.get('expression')


class CompositeFact(object):
    def __init__(self, protocol, data):
        self.id = data['id']
        self.operator = data['operator']
        self.facts = [protocol.facts[fact_id] for fact_id in data['facts'] if fact_id in protocol.facts]


class Protocol(object):
    FACT_MAP = { 
        'entity_fact': EntityFact
    }

    def __init__(self, data):
        self.facts = {}
        self.terminals = []

        for fact in data['facts']:
            f = self.FACT_MAP.get(fact['type'])
            if f:
                self.facts[fact['id']] = f(fact)

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


class AndOperator(calc_graph.CGOperator):
    op_name = 'AND'

    def calc(self, children=None, input_val=None):
        return all([ch.value for ch in children])

    def confidence(self, children=None):
        return reduce(lambda x, y: x * y, [c.confidence for c in children])


class OrOperator(calc_graph.CGOperator):
    op_name = 'OR'

    def calc(self, children=None, input_val=None):
        return any([ch.value for ch in children])

    def confidence(self, children=None):
        return max([ch.confidence for ch in children])


class ConvoFact(calc_graph.CGNode):

    def __init__(self, protocol, fact, parents=None, barzer_svc=None):
        super(ConvoFact, self).__init__()
        self.value = False
        self.confidence = 0
        self.id = fact.id
        self.parents = set(parents or [])
        self.protocol = protocol

        if barzer_svc:
            self.barzer_svc = barzer_svc
        elif parents:
            self.barzer_svc = parents[0].barzer_svc
        else:
            self.barzer_svc = protocol.barzer_svc

    def remove_parent(self, _id):
        if _id in self.parents:
            self.parents.remove(_id)

    def add_parent(self, p):
        self.parents.add(p)

    def update(self, entity, value=None, confidence=None):
        val, conf = self.value, self.confidence

        if value:
            self.value = value
        if confidence:
            self.confidence = confidence

        if self.value != val or self.confidence != conf:
            for parent in self.parents:
                parent.pq[self] = self.score()
                self.protocol.add_fact_to_update(parent)

            if self.value is False and self.children:
                for ch in self.children:
                    ch.remove_parent(self.id)

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


class ConvoEntityFact(ConvoFact):
    def __init__(self, protocol, fact, parents=None, barzer_svc=None):
        super(ConvoEntityFact).__init__(protocol, fact, parents, barzer_svc)
        self.ent = cg_ent_fact.CGEntityNode(ent=fact.entity, expression=fact.expression, ent_question=fact.question, barzer_svc=self.barzer_svc)

        def step(self, input_val=None):
            resp = self.ent.step(input_val)
            self.update(value=self.ent.value, confidence=self.ent.confidence)
            return resp

        def analyze_beads(self, beads):
            self.ent.analyze_beads(beads)
            self.update(value=self.ent.value, confidence=self.ent.confidence)

        def score(self):
            if self.value.is_set():
                return 0
            else:
                return self.confidence


class ConvoCompositeFact(ConvoFact):
    OPERATOR_MAP = {
        'AND': AndOperator,
        'OR': OrOperator,
    }

    def __init__(self, protocol, fact, parents=None, barzer_svc=None):
        super(ConvoCompositeFact, self).__init__(protocol, fact, parents, barzer_svc=barzer_svc)

        op = self.OPERATOR_MAP.get(fact.operator)
        if op:
            self.op = op()

        self.pq = pqdict.maxpq()
        self.set_children([
            protocol.create_or_update_fact(
                protocol, f, [self]) for f in fact.facts])

        self.value = self.op.calc(children=self.get_children())
        self.confidence = self.op.confidence(children=self.get_children())

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

    def current_child(self):
        return self.pq.top()

    def update(self):
        value = self.op.calc(children=self.get_children())
        confidence = self.op.calc(children=self.get_children())
        super(ConvoCompositeFact).update(value, confidence)

    def score(self):
        if self.value.is_set():
            return 0
        else:
            return self.confidence


class ConvoProtocol(calc_graph.CGNode):
    FACT_MAP = {
        CompositeFact: ConvoCompositeFact,
        EntityFact: ConvoEntityFact
    }

    def __init__(self, protocol, barzer_svc=None):
        super(ConvoProtocol, self).__init__()
        self.terminals = {}
        self.facts_ = {}
        self.barzer_svc = barzer_svc or barzer.barzer_svc.barzer

        self.visited_facts = set()
        self.facts_to_update = deque()

        for t in protocol.terminals:
            self.terminals[t.id] = ConvoCompositeFact(protocol=self, fact=t, parents=[self])

        self.set_children(self.terminals.values())
        self.pq = pqdict.maxpq()
        for t in self.terminals.values():
            self.pq[t] = t.score()

    def extract_entities(self, input_val=None):  # TODO
        res = []
        for token in input_val.split():
            if token in self.entities:
                res.append(self.entities[token])
        return res

    def create_or_update_fact(self, protocol, f, parents):
        if f.id in self.facts_:
            self.facts_[f.id].add_parents(parents)
        else:
            _type = self.FACT_MAP.get(f)
            if _type:
                self.facts[f.id] = _type(protocol, f, parents)

        return self.facts_[f.id]

    def add_fact_to_update(self, fact):
        if fact.id not in self.visited_facts:
            self.to_update.append(fact)
            self.visited_facts.add(fact.id)

    def update_facts(self):
        while len(self.facts_to_update) > 0:
            f = self.facts_to_update.popleft()
            f.update()
        self.visited_facts = set()

    def step(self, input_val=None):
        if input_val:
            beads = barzer_objects.BeadFactory.make_beads_from_barz(self.barzer_svc.get_json(input_val))
            for f in self.facts.values():
                if isinstance(f, ConvoEntityFact):
                    f.analyze_beads(beads)

        resp = self.current_child().step(input_val)

        for _id, t in self.terminals.items():
            print _id, t.value.is_true()
            if t.value.is_true():
                return "You have " + _id

        return resp

    def current_child(self):
        return self.pq.top()
