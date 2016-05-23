# pylint: disable=missing-docstring, invalid-name, trailing-whitespace, line-too-long
from collections import defaultdict, deque
from toposort import toposort
from lib import cg_ent_fact
from lib.barzer import barzer_objects
from lib.barzer.barzer_svc import barzer as default_barzer_instance
import pqdict
from lib import calc_graph


class Fact(object):
    def __init__(self, data, protocol=None):
        self.id = data['id']
        self.question = ''


class EntityFact(Fact):
    def __init__(self, data, protocol=None):
        super(EntityFact, self).__init__(data)
        self.entity = barzer_objects.Entity(data['entity'])
        self.question = data.get('question')
        self.expression = data.get('expression')


class CompositeFact(Fact):
    def __init__(self, data, protocol=None):
        self.id = data['id']
        self.question = ''
        self.operator = data['operator']
        if protocol:
            self.facts = [protocol.facts[fact_id] for fact_id in data['facts'] if fact_id in protocol.facts]


class Protocol(object):
    FACT_MAP = { 
        'entity': EntityFact,
        'composite': CompositeFact,
        None: Fact
    }

    def __init__(self, data):
        self.facts = {}

        # topologically sorting facts 
        G = defaultdict(set)
        for fact in data['facts']:
            self.facts[fact['id']] = fact
            if fact.get('facts'):
                for dependant_fact_id in fact['facts']:
                    G[fact['id']].add(dependant_fact_id)

        for facts_of_equal_priority in toposort(G):
            for fact_id in facts_of_equal_priority:
                fact = self.facts[fact_id]
                _type = self.FACT_MAP.get(fact.get('node_type'))
                self.facts[fact_id] = _type(fact, protocol=self)

        self.terminals = set(self.facts[t] for t in data['terminals'])


class AndOperator(calc_graph.CGOperator):
    op_name = 'AND'

    def calc(self, children=None, input_val=None):
        value = calc_graph.CGNodeValue()
        if all([ch.value.is_true() for ch in children]):
            value.set_val(True)
        elif any([ch.value.is_false] for ch in children):
            value.set_val(False)
        return value

    def confidence(self, children=None):
        return reduce(lambda x, y: x * y, [c.confidence for c in children])


class OrOperator(calc_graph.CGOperator):
    op_name = 'OR'

    def calc(self, children=None, input_val=None):
        value = calc_graph.CGNodeValue()
        if any([ch.value.is_true() for ch in children]):
            value.set_val(True)
        elif all([ch.value.is_false() for ch in children]):
            value.set_val(False)
        return value

    def confidence(self, children=None):
        return max([ch.confidence for ch in children])


class ConvoFact(calc_graph.CGNode):

    def __init__(self, protocol, fact, parents=None, barzer_svc=None):
        super(ConvoFact, self).__init__()
        self.confidence = 0
        self.id = fact.id
        self.question = fact.question
        self.parents = set(parents or [])
        self.protocol = protocol

        if barzer_svc:
            self.barzer_svc = barzer_svc
        elif parents:
            self.barzer_svc = parents[0].barzer_svc
        else:
            self.barzer_svc = protocol.barzer_svc

    def step(self, input_val=None):
        return calc_graph.CGStepResponse(
            text=self.question
        )

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
        super(ConvoEntityFact, self).__init__(protocol, fact, parents, barzer_svc)
        self.ent = cg_ent_fact.CGEntityNode(data=fact.entity, expression=fact.expression, ent_question=fact.question, barzer_svc=self.barzer_svc)

        def step(self, input_val=None):
            resp = self.ent.step(input_val)
            self.update(value=self.ent.value, confidence=self.ent.confidence)
            return resp

        def analyze_beads(self, beads):
            self.ent.analyze_beads(beads)
            self.update(value=self.ent.value, confidence=self.ent.confidence)

        def analyze_input(self, input_val):
            return self.analyze_beads(self.barzer_svc.get_beads(input_val))

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

    def __init__(self, data, barzer_svc=None):
        protocol = Protocol(data)

        super(ConvoProtocol, self).__init__()
        self.terminals = {}
        self.facts = defaultdict(set)
        self.barzer_svc = barzer_svc or default_barzer_instance

        self.visited_facts = set()
        self.facts_to_update = deque()

        for t in protocol.terminals:
            self.terminals[t.id] = ConvoCompositeFact(protocol=self, fact=t, parents=[self])

        self.set_children(self.terminals.values())
        self.pq = pqdict.maxpq()
        for t in self.terminals.values():
            self.pq[t] = t.score()

    def create_or_update_fact(self, protocol, f, parents):
        if f.id in self.facts:
            self.facts[f.id].add_parents(parents)
        else:
            _type = self.FACT_MAP.get(f.__class__)
            if _type:
                self.facts[f.id] = _type(protocol, f, parents)
                self.facts[_type].add(f)

        return self.facts[f.id]

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
            for f in self.facts[ConvoEntityFact]:
                f.analyze_input(input_val)

        resp = self.current_child().step(input_val)

        for _id, t in self.terminals.items():
            print _id, t.value.is_true()
            if t.value.is_true():
                return calc_graph.CGStepResponse(
                    text="You have " + _id
                )

        return resp

    def current_child(self):
        return self.pq.top()
