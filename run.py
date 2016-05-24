from flask import Flask
from flask import request, abort
import json
import uuid
from lib import convo_fact, calc_graph

app = Flask(__name__)
protocol_data = {'test': json.load(open('lib/tests/test.json'))}
conversations = {}


def init_convo(protocol_name):
    token = str(uuid.uuid4())
    cg = calc_graph.CG()
    cg.root = convo_fact.ConvoProtocol(protocol_data[protocol_name])
    conversations[token] = cg
    return token


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
    app.run(debug=True)
