from sdk import ZobotClient

zobot = ZobotClient('http://localhost:5000')
zobot.set_protocol(zobot.get_available_protocols()[0])

user_input = ''
while True:
    user_input = raw_input(zobot.say(user_input))
