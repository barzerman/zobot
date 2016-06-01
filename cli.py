from sdk import ZobotClient

zobot = ZobotClient()
zobot.set_protocol(zobot.get_available_protocols()[0])

user_input = ''
while True:
    user_input = raw_input(zobot.say(user_input))
