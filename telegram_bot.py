import telebot
from sdk import ZobotClient

# telegram.me/zobot_test_bot
bot = telebot.TeleBot("208359220:AAGAXDsRRiFzaPjwSztv6sH8Httqqg660ow")
zobot = ZobotClient()

available_protocols = zobot.get_available_protocols()
protocols_msg = '/n'.join(['/' + x for x in available_protocols])


@bot.message_handler(commands=['start'])
def send_welcome(message):
    zobot.reset()
    bot.reply_to(message, "Hi! What protocol do you want to use?\n" + protocols_msg)


@bot.message_handler(commands=available_protocols)
def init_protocol(message):
    print message.text
    try:
        zobot.init_from_external(message.text.split('/')[-1], 'telegram:' + str(message.chat.id))
        bot.reply_to(message, zobot.say())
    except:
        bot.reply_to(message, 'Can not initialize protocol')


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if zobot.token:
        bot.reply_to(message, zobot.say(message.text))
    else:
        bot.reply_to(message, 'No protocol is selected. Please select one of the protocols:\n' + protocols_msg)

bot.polling()
