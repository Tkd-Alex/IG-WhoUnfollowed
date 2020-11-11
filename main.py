#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import _thread
import os
import json
import pickle
import random
import time
import logging
import datetime

from telegram.ext import Updater, CommandHandler, Job, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from configparser import ConfigParser
from pprint import pprint
from pymongo import MongoClient

from igsentinel import Sentinel

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(name)s - [%(funcName)s]: %(message)s", datefmt="%d/%m/%Y %H:%M:%S", level=logging.INFO)
logger = logging.getLogger("TELEGRAM-BOT")

config = ConfigParser()
config.read("./config.ini")

telegram_token = config.get("telegram", "token")
sentinel_username = config.get("igsentinel", "username")
sentinel_password = config.get("igsentinel", "password")

client = MongoClient("localhost", 27017)
db = client["whounfollowed"]


def help_method(update, context):
    update.message.reply_text("Hi! Use /track <igpage> to start tracking of your followers.")


def track(update, context):
    if len(context.args) == 1:
        igpage = context.args[0]
        alreadyexist = db.users.find_one({"igpage": igpage})
        if alreadyexist is None:
            update.message.reply_text("Please wait 1/2 minutes... We are checking the page <b>{}</b>".format(igpage), parse_mode="HTML")

            logger.info("Start sentinel for igpage={}".format(igpage))
            sentinel = Sentinel(sentinel_username, sentinel_password, nogui=True, headless_browser=False)
            sentinel.login()
            result, message = sentinel.checkuser(igpage)
            logger.info("Result check followers for igpage={}, result={}, message={}".format(igpage, result, message))

            if result is True:
                user = {"chat_id": [update.message.chat_id], "igpage": igpage, "followers": [], "last_update": None}
                db.users.insert_one(user)

            update.message.reply_text(message)
            _thread.start_new_thread(
                _thread_sentinel,
                (
                    context.bot,
                    user,
                ),
            )
            sentinel.end()
        else:
            if update.message.chat_id in alreadyexist["chat_id"]:
                update.message.reply_text("Sorry but you are already tracking <b>{}</b>".format(igpage), parse_mode="HTML")
            else:
                db.users.update_one({"_id": alreadyexist["_id"]}, {"$push": {"chat_id": update.message.chat_id}})
                update.message.reply_text("Another telegram user is tracking <b>{}</b>. Both will receive the notification".format(igpage), parse_mode="HTML")
    else:
        update.message.reply_text("Wrong input! Usage: /track igpage.\nExample: /track <b>tkd_alex</b>", parse_mode="HTML")


def _thread_sentinel(bot, user):
    while True:
        try:
            logger.info("Start sentinel thread for igpage={}".format(user["igpage"]))
            if  user["last_update"] is None or (datetime.datetime.now() - user["last_update"]).total_seconds() / 60 >= 50:
                sentinel = Sentinel(sentinel_username, sentinel_password, nogui=True, headless_browser=False)
                login = sentinel.login()
                logger.info("Sentinel login={}, igpage={}".format(login, user["igpage"]))
                followers_list = sentinel.listfollowers(user["igpage"])
                logger.info("Sentinel followers list complete, igpage={}, len={}".format(user["igpage"], len(followers_list)))
                sentinel.end()

                # Update database record ...
                db.users.update_one({"_id": user["_id"]}, {"$set": {"last_update": datetime.datetime.now()}})
                user = db.users.find_one({"_id": user["_id"]})

                if os.path.isfile("followers/{}.txt".format(user["igpage"])) is False:  # First time...
                    with open("followers/{}.txt".format(user["igpage"]), "w+") as f:
                        f.write("\n".join(followers_list)) # + "\n")
                    history_followers = []
                else:
                    with open("followers/{}.txt".format(user["igpage"]), "r") as f:
                            history_followers = f.readlines()
                    history_followers = [item.lower().replace("\n", "").strip() for item in history_followers]
                    followers_update = list(set(history_followers + followers_list))
                    with open("followers/{}.txt".format(user["igpage"]), "w+") as f:
                        f.write("\n".join(followers_update)) # + "\n")

                if followers_list != []:
                    if history_followers == []:
                        for chat_id in user["chat_id"]:
                            bot.send_message(chat_id, text="Successfully downloaded all of your <b>{}</b> followers".format(len(followers_list)), parse_mode="HTML")
                    else:
                        message = ""
                        for username in history_followers:  # Check current username
                            if not username in followers_list:
                                message += '<a href="https://instagram.com/{0}">{0}</a>\n'.format(username)

                        if message != "":
                            message = "Dear {}, {} account have unfollowed you!\n".format(user["igpage"], len(message.split("\n")) - 1) + message
                            logger.info("{}".format(message))
                            for chat_id in user["chat_id"]:
                                bot.send_message(chat_id, text=message, parse_mode="HTML", disable_web_page_preview=True)
        except Exception as e:
            logger.error("Exception raised: {}".format(e))

        time.sleep(60 * random.uniform(53, 260))


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


if __name__ == "__main__":
    if not os.path.exists("followers/"):
        os.makedirs("followers/")

    updater = Updater(telegram_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", help_method))
    dispatcher.add_handler(CommandHandler("help", help_method))

    dispatcher.add_handler(CommandHandler("track", track, pass_args=True))

    users = db.users.find({}, {"chat_id": 0})
    for user in users:
        _thread.start_new_thread(
            _thread_sentinel,
            (
                dispatcher.bot,
                user,
            ),
        )

    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()
