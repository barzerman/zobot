from lib import calc_graph
from lib import convo_fact
import json

data = json.load(open('protocols/test2.json'))
cg = calc_graph.CG(data)
print cg.root.to_dict()