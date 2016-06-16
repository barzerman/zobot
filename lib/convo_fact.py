# pylint: disable=missing-docstring, invalid-name, line-too-long
from collections import defaultdict, deque
import pqdict
from toposort import toposort
from lib import cg_ent_fact
from lib.barzer.barzer_svc import barzer as default_barzer_instance
from lib import calc_graph
from lib import cg_index


class Fact(object):
    def __init__(self, data, protocol=None):
        self.id = data['node_id']
        self.question = data.get('question')


class EntityFact(Fact):
    def __init__(self, data, protocol=None):
        super(EntityFact, self).__init__(data)
        self.entity = data['data']


class CompositeFact(Fact):
    def __init__(self, data, protocol=None):
        super(CompositeFact, self).__init__(data, protocol)
        self.operator = data['operator']
        self.text = data['text']
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
            self.facts[fact['node_id']] = fact
            if fact.get('facts'):
                for dependant_fact_id in fact['facts']:
                    G[fact['node_id']].add(dependant_fact_id)

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
        elif any([ch.value.is_false() for ch in children]):
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
        self.confidence = 0.5
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

    def activate(self):
        self.current_child().activate()

    def remove_parent(self, _id):
        if _id in self.parents:
            self.parents.remove(_id)

    def add_parent(self, p):
        self.parents.add(p)

    def update(self, value, confidence):
        if not self.value.equal(value) or self.confidence != confidence:
            self.value = value
            self.confidence = confidence

            for parent in self.parents:
                parent.pq[self] = self.score()
                self.protocol.add_fact_to_update(parent)

            if self.value.is_false() and self.children:
                for ch in self.children:
                    ch.remove_parent(self.id)

    def score(self):
        if self.value.is_set():
            return 0
        else:
            return len(self.parents)

    def to_dict(self):
        data = {'id': self.id, 'value': self.value.to_dict(), 'confidence': self.confidence}
        if self.children:
            data['children'] = [c.to_dict() for c in self.children]
        return data


class ConvoEntityFact(ConvoFact):
    def __init__(self, protocol, fact, parents=None, barzer_svc=None):
        super(ConvoEntityFact, self).__init__(protocol, fact, parents, barzer_svc)
        self.ent = cg_ent_fact.CGEntityNode(data=fact.entity, barzer_svc=self.barzer_svc)
        self.index = self.protocol.index
        self.index.add(self)

    def ent_id(self):
        return self.ent.ent_id()

    def __str__(self):
        return str(self.ent)

    def step(self, input_val=None):
        resp = self.ent.step(input_val)
        self.update(value=self.ent.value, confidence=self.ent.confidence)
        return resp

    def activate(self):
        for fact in self.index.get(self.ent_id()):
            fact.ent.activate()

    def deactivate(self):
        self.ent.deactivate()

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
        self.text = fact.text

        op = self.OPERATOR_MAP.get(fact.operator)
        if op:
            self.op = op()

        self.pq = pqdict.maxpq()
        self.set_children([
            protocol.create_or_update_fact(f, [self]) for f in fact.facts])

        self.value = self.op.calc(children=self.get_children())
        self.confidence = self.op.confidence(children=self.get_children())

    def set_children(self, children):
        self._nodes = {}
        for ch in children:
            self.pq[ch] = 0
            self._nodes[ch.id] = ch
        super(ConvoCompositeFact, self).set_children(children)

    def current_child(self):
        return self.pq.top()

    def update(self):
        value = self.op.calc(children=self.get_children())
        if value.is_set():
            confidence = 1.0
        else:
            confidence = self.op.confidence(children=self.get_children())
        super(ConvoCompositeFact, self).update(value, confidence)

    def score(self):
        if self.value.is_set():
            return 0
        else:
            return self.confidence

    def step(self, input_val=None):
        return self.current_child().step(input_val)


class ConvoProtocol(calc_graph.CGNode):
    node_type_id = 'convo_protocol'

    FACT_MAP = {
        CompositeFact: ConvoCompositeFact,
        EntityFact: ConvoEntityFact
    }

    def __init__(self, data, barzer_svc=None):
        protocol = Protocol(data)
        self.id = 'protocol'
        self.index = cg_index.Index()

        super(ConvoProtocol, self).__init__()
        self.terminals = {}
        self.facts = defaultdict(set)
        self.barzer_svc = barzer_svc or default_barzer_instance

        self.visited_facts = set()
        self.facts_to_update = deque()

        for t in protocol.terminals:
            self.facts[t.id] = self.terminals[t.id] = ConvoCompositeFact(protocol=self, fact=t, parents=[self])

        self.set_children(self.terminals.values())
        self.pq = pqdict.maxpq()
        for t in self.terminals.values():
            self.pq[t] = t.score()

    def create_or_update_fact(self, f, parents):
        if f.id in self.facts:
            self.facts[f.id].add_parents(parents)
        else:
            _type = self.FACT_MAP.get(f.__class__)
            if _type:
                self.facts[f.id] = _type(self, f, parents)
                self.facts[_type].add(self.facts[f.id])

        return self.facts[f.id]

    def get_nodes(self):
        res = {}
        for k, v in self.facts.iteritems():
            if isinstance(v, calc_graph.CGNode):
                res[k] = v
        return res

    def add_fact_to_update(self, fact):
        if fact.id not in self.visited_facts:
            self.facts_to_update.append(fact)
            self.visited_facts.add(fact.id)

    def update_facts(self):
        while len(self.facts_to_update) > 0:
            f = self.facts_to_update.popleft()
            if not f.id == self.id:
                f.update()
        self.visited_facts = set()

    def step(self, input_val=None):
        self.current_child().activate()

        if input_val:
            for f in self.facts[ConvoEntityFact]:
                f.analyze_input(input_val)
                f.deactivate()
        self.update_facts()

        resp = self.current_child().step()

        for _id, t in self.terminals.items():
            if t.value.is_true():
                self.value.set_val(True)
                return calc_graph.CGStepResponse(
                    text=t.text
                )

        return resp

    def current_child(self):
        return self.pq.top()
