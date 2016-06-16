from flask import Flask
from flask import request, abort
import json
import uuid
from glob import glob
from lib import calc_graph
from lib import convo_fact


class ZobotServer(object):
    def __init__(self, protocols_path='protocols/'):
        self.protocol_data = {}
        self.conversations = {}

        for p_name in glob(protocols_path + '*.json'):
            try:
                self.protocol_data[p_name.split('/')[-1].split('.')[0]] = json.load(open(p_name))
                print 'loaded protocol', p_name
            except Exception, e:
                print 'can not load protocol', p_name, e

    def init_convo(self, protocol_name, external_token=None):
        if protocol_name in self.protocol_data:
            if external_token:
                token = external_token
            else:
                token = str(uuid.uuid4())
            cg = calc_graph.CG(self.protocol_data[protocol_name])
            self.conversations[token] = cg
            return token
        else:
            raise Exception('protocol not found') 

    def drop_convo(self, token):
        if token in self.conversations:
            del self.conversations[token]
            return 'ok'
        else:
            raise Exception('conversation not found')

    def say(self, token, input=''):
        if token in self.conversations:
            value, resp = self.conversations[token].step(input)
            return resp.text
        else:
            raise Exception('conversation not found')

    def available_protocols(self):
        return self.protocol_data.keys()

zobot = ZobotServer()
app = Flask(__name__)


@app.route("/discover")
def discover():
    return json.dumps(zobot.available_protocols())


@app.route("/protocol/<protocol>/init")
def login(protocol):
    return zobot.init_convo(protocol)


@app.route("/protocol/<protocol>/init/<external_token>")
def login_with_token(protocol, external_token):
    return zobot.init_convo(protocol, external_token)


@app.route("/convo/<token>/say")
def say(token):
    # try:
    return zobot.say(token, request.args.get('input', ''))
    # except:
    #     abort(404)


@app.route("/convo/<token>/drop")
def drop(token):
    try:
        return zobot.drop_convo(token)
    except:
        abort(404)

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)
