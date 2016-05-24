from flask import Flask
from flask import request, abort
import json
import uuid
from glob import glob
from lib import convo_fact, calc_graph

app = Flask(__name__)
protocol_data = {}
conversations = {}


def init_protocol_data(path):
    for p_name in glob(path + '*.json'):
        try:
            protocol_data[p_name.split('/')[-1].split('.')[0]] = json.load(open(p_name))
            print 'loaded protocol', p_name
        except Exception, e:
            print 'can not load protocol', p_name, e


def init_convo(protocol_name):
    token = str(uuid.uuid4())
    cg = calc_graph.CG()
    cg.root = convo_fact.ConvoProtocol(protocol_data[protocol_name])
    conversations[token] = cg
    return token


@app.route("/discover")
def available_protocols():
    return json.dumps(protocol_data.keys())


@app.route("/protocol/<protocol>/init")
def login(protocol):
    if protocol in protocol_data:
        token = init_convo(protocol)
        return token
    else:
        abort(404)


@app.route("/convo/<token>/say")
def say(token):
    if token in conversations:
        input_val = request.args.get('input', '')
        value, resp = conversations[token].step(input_val)
        return resp.text
    else:
        abort(404)


@app.route("/convo/<token>/drop")
def drop(token):
    if token in conversations:
        del conversations[token]
        return 'ok'
    else:
        abort(404)

if __name__ == "__main__":
    init_protocol_data('lib/tests/')
    app.run(debug=True)
