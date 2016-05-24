import requests
import json


class ZobotClient(object):
    def __init__(self, zobot_url='http://localhost:5000'):
        self.url = zobot_url
        self.token = None

    def get_available_protocols(self):
        resp = requests.get(self.url + '/discover')
        if resp.status_code == requests.codes.ok:
            return json.loads(resp.text)
        else:
            raise Exception(resp.text)

    def set_protocol(self, protocol_name):
        resp = requests.get('/'.join([self.url, 'protocol', protocol_name, 'init']))
        if resp.status_code == requests.codes.ok:
            self.token = resp.text
        else:
            raise Exception(resp.text)

    def init_from_external(self, protocol_name, external_token):
        resp = requests.get('/'.join([self.url, 'protocol', protocol_name, 'init', external_token]))
        if resp.status_code == requests.codes.ok:
            self.token = resp.text
        else:
            raise Exception(resp.text)

    def say(self, input=''):
        resp = requests.get(self.url + '/convo/' + self.token + '/say', params={'input': input})
        if resp.status_code == requests.codes.ok:
            return resp.text + '\n'
        else:
            raise Exception(resp.text)

    def reset(self):
        if self.token:
            requests.get(self.url + '/convo/' + self.token + '/drop')
            self.token = None
