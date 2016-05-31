from lib import calc_graph
from lib import cg_ent_fact
from lib.barzer.barzer_svc import barzer
from lib.barzer import barzer_objects
class Runner(object):
    DEFAULT_DATA = {
        'headache': {
            'class': 459,
            'subclass': 3,
            'id': 'HEADACHE',
            'name': 'Headache'
        },
        'temperature': {
            'class': 459,
            'subclass': 9,
            'id': 'temperature',
            'name': 'Temperature',
            'expression': {'op': '>', 'values': 200},
            'node_id': 'node.temperature',
            'value_type': {
                'type': 'number',
                'lo': 50,
                'hi': 350,
            }       
        }
    }
    def __init__(self, data=None):
        self.cg = calc_graph.CG([{'node_type': 'entity', 'data': data or self.DEFAULT_DATA['temperature']}])
