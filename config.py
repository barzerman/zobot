class BarzerSettings(object):
    # available instances of Barzer
    BARZER_INSTANCES = {
        'default' : {
            'url': 'https://my.barzer.net/query/json',
            'key': 'yTIzlFaf02QBBa3wRNPD2xjeI0R1P1hPHwL3dHtv'
        }
    }

class RulesSettings(object):
    RULES_STRATEGY = {}
    RULES_FILES = []
    STAGES = [
        {'name': 'representation'},
        {'name': 'diagnostic'},
        {'name': 'personal details'},
    ]
    YES_ENTITY = {
        "class": 1,
        "scope": "Generic",
        "category": "eng_convo",
        "subclass": 105,
        "id": "YES",
        "name": "yes",
    }
    NO_ENTITY = {
        "class": 1,
        "scope": "Generic",
        "category": "eng_convo",
        "subclass": 105,
        "id": "NO",
        "name": "no",
    }

