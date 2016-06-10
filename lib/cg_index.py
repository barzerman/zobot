from collections import defaultdict


class Index(object):

    def __init__(self):
        self.__store = defaultdict(set)

    def add(self, entity_fact):
        self.__store[entity_fact.ent_id()].add(entity_fact)

    def get(self, ent_id):
        return self.__store[ent_id]

    def __str__(self):
        return str(self.__store)
