from lib import calc_graph

class ConvoSimpleFactEstablishOP(calc_graph.CGOperator):
    """ queries Barzer to extract needed entities """
    # TODO: override calc

class ConvoSimpleFactNode(calc_graph.CGNode):
    """ an arithmetic expression over simple
    fact(s) - can be entities and such
    """
    # TODO: override step
