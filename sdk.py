import requests
import json


class ZobotClient(object):
    def __init__(self, zobot_url='http://localhost:5000'):
        self.url = zobot_url

    def get_available_protocols(self):
        return json.loads(requests.get(self.url + '/discover').text)

    def set_protocol(self, protocol_name):
        self.token = requests.get('/'.join([self.url, 'protocol', protocol_name, 'init'])).text

    def say(self, input=''):
        return requests.get(self.url + '/convo/' + self.token + '/say', params={'input': input}).text + '\n'
