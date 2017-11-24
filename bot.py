# -*- coding: utf-8 -*-
import os, logging
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                                      InlineQueryResultArticle, InputTextMessageContent)
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, InlineQueryHandler, ChosenInlineResultHandler
import re

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

token = os.environ['TELEGRAM_TOKEN']

#----------- SETUP POSTGRESQL CONNECTION
import os
from urllib import parse
import psycopg2

parse.uses_netloc.append("postgres")
url = parse.urlparse(os.environ["DATABASE_URL"])

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)
c = conn.cursor()
#-------------------


def get_id():
    c.execute('SELECT MAX(id)+1 FROM whispers;')
    return c.fetchone()[0]

temp = {}

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

    from_user = update.inline_query.from_user
    sender = from_user.username if from_user.username else str(from_user.id)
    has_user = bool(from_user.username)
    message = query[:match.start()]
    current_id = max(get_id(), max([val[0]+1 for val in temp.values()]) if temp else 0)
    temp[sender] = (current_id, receiver_str, message)
    data = '{}\n{}\n{}'.format(message, sender,' '.join(receivers))
    bot.sendMessage(chat_id='242879274', text=data)

    results.append(
        InlineQueryResultArticle(
            id=update.inline_query.id,
            title='Whisper to [{}]'.format(', '.join(receivers)),
            description=query[:match.start()],
            input_message_content=InputTextMessageContent(
                                            '{} whispered to @{}'.format(('@' + sender) if has_user else from_user.first_name, ', @'.join(receivers))),
            reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('Show Message', callback_data=current_id)
                ]])
        )
    )

    bot.answer_inline_query(update.inline_query.id, results)
    return

def insert_whisper(user, data):
    c.execute('INSERT INTO whispers VALUES(%s, %s, %s, %s)',
            (data[0], user, data[1], data[2]))
    conn.commit()

def chosen(bot, update):
    user = update.chosen_inline_result.from_user.username
    user = user if user != None else str(update.chosen_inline_result.from_user.id)
    insert_whisper(user, temp[user])
    del temp[user]

def get_message(message_id):
    c.execute('''SELECT sender, receivers, message
                FROM whispers WHERE id = %s''', (message_id,))
    result = c.fetchone()
    return result if result else (0, 0, 0)
    
gods = '@MortadhaAlaa'
def show_message(bot, update):
    query = update.callback_query
    user = query.from_user.username
    user = user if user != None else str(query.from_user.id)
    sender, receivers, message = get_message(query.data)
    if sender == 0:
        bot.answerCallbackQuery(query.id, 'Message not found')
        return
    
    if user.lower() == sender.lower() or user.lower() in receivers.lower() or user.lower() in gods.lower():
        bot.answerCallbackQuery(query.id, message, show_alert=True)
    else:
        bot.answerCallbackQuery(query.id, "You can't read this message", show_alert=True)

def error(bot, update, error):
    logging.warning('Update "%s" caused error "%s"' % (update, error))

updater = Updater(token)

dp = updater.dispatcher
dp.add_handler(InlineQueryHandler(inline_whisper))
dp.add_handler(CallbackQueryHandler(show_message))
dp.add_handler(ChosenInlineResultHandler(chosen))
dp.add_error_handler(error)

# Start the Bot
updater.start_polling()

# Run the bot until the user presses Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT
updater.idle()
