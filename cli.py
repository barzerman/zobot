import requests

url = 'http://localhost:5000'
protocol = 'test'

token = requests.get('http://localhost:5000/protocol/test/init').text


def get_bot_phrase(input=''):
    return requests.get('http://localhost:5000/convo/' + token + '/say', params={'input': input}).text + '\n'

user_input = ''
while True:
    user_input = raw_input(get_bot_phrase(user_input))
