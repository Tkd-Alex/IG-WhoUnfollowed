#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import _thread, json, pickle, random
from time import sleep, clock
from datetime import datetime
from telegram.ext import Updater, CommandHandler, Job, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from configparser import SafeConfigParser
from pprint import pprint
from pymongo import MongoClient
from igsentinel import Sentinel

config = SafeConfigParser()
config.read('./config.ini')

telegram_token = config.get('telegram', 'token')
sentinel_username = config.get('igsentinel', 'username')
sentinel_password = config.get('igsentinel', 'password')

client = MongoClient('localhost', 27017)
db = client['whounfollowed']

def help(bot, update):
    update.message.reply_text('Hi! Use /track <igpage> to start tracking of your followers.')

def track(bot, update, args):
    if len(args) == 1:
        igpage = args[0]
        alreadyexist = db.users.find_one({'igpage': igpage})
        if alreadyexist is None:
            update.message.reply_text('Please wait 1/2 minutes... We are checking the page <b>{}</b>'.format(igpage), parse_mode='HTML')
            
            print("{}\t Start sentinel for igpage={}".format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), igpage))
            s = Sentinel(sentinel_username, sentinel_password, nogui=True, headless_browser=True)
            s.login()
            result, message = s.checkuser(igpage)
            print("{}\t Result check followers for igpage={}, result={}, message={}".format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), igpage, result, message))
            
            if result is True:
                user = {
                    'chat_id': [update.message.chat_id],
                    'igpage': igpage,
                    'followers': []
                }
                db.users.insert_one(user)
            
            update.message.reply_text(message)
            _thread.start_new_thread(sentinelThread, (bot, user, ) )
            s.end()
        else:
            if update.message.chat_id in alreadyexist['chat_id']:
                update.message.reply_text('Sorry but you are already tracking <b>{}</b>'.format(igpage), parse_mode='HTML')
            else:
                db.users.update_one({"_id": alreadyexist['_id']}, {'$push': {'chat_id': update.message.chat_id}})
                update.message.reply_text('Another telegram user is tracking {}. Both will receive the notification'.format(igpage))
    else:
        update.message.reply_text('Wrong input! Usage: /track igpage.\nExample: /track <b>tkd_alex</b>', parse_mode='HTML')

def sentinelThread(bot, user):
    while True:
        print("{}\t Start sentinel thread for igpage={}".format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), user['igpage']))
        s = Sentinel(sentinel_username, sentinel_password, nogui=True, headless_browser=True)
        s.login()
        fwlist = s.listfollowers(user['igpage'])
        print("{}\t Sentinel followers list complete, len={}".format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), len(fwlist)))
        s.end()
        user = db.users.find_one({"_id": user['_id']})
        message = ""
        for fw in user['followers']:
            if not fw in fwlist:
                message += '<a href="https://instagram.com/{}">{}</a>\n'.format(fw, fw)
        if not message == "":
            message = "{} account have unfollowed you!\n".format(len(message.split('\n'))-1) + message
            for chat_id in user['chat_id']:
                bot.send_message(chat_id, text=message, parse_mode='HTML')

        db.users.update_one({"_id": user['_id']}, {"$set": {"followers": fwlist} })
        #sleep(300) # 5minutes
        sleep(random.randint(3200, 4000)) # range(53m, 66m)

def main():
    updater = Updater(telegram_token)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", help))
    dp.add_handler(CommandHandler("help", help))

    dp.add_handler(CommandHandler("track", track, pass_args=True))

    users = db.users.find({}, {"followers": 0, "chat_id": 0})
    for user in users:
        _thread.start_new_thread(sentinelThread, (dp.bot, user, ) )

    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()