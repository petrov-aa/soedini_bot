import logging
import os
import requests
import shutil
from telebot import TeleBot, apihelper, logger
from telebot.apihelper import ApiException

from . import process
from .database import commit_session, flush_session
from .config import bot_config, proxy_config, tmp_dir
from .models import Chat, Message, Image, CHAT_STATE_WAIT_IMAGES
from .messages import *

bot = TeleBot(bot_config['token'], threaded=False)

combined_image_path_template = tmp_dir + '/combined_%d.jpg'

proxy_urls = {'https': '%s://%s:%s@%s:%s' % (proxy_config['protocol'],
                                             proxy_config['user'],
                                             proxy_config['password'],
                                             proxy_config['host'],
                                             proxy_config['port'])} if bot_config['use_proxy'] else {}

logger.setLevel(logging.DEBUG)

if bot_config['use_proxy']:
    apihelper.proxy = proxy_urls


@bot.message_handler(commands=['start', 'cancel'])
def send_start(message):
    with commit_session() as session:
        chat = Chat.get_by_telegram_id(message.chat.id)
        restart(chat)
        bot.send_message(chat.telegram_id, BOT_START)


@bot.message_handler(commands=['help'])
def send_start(message):
    with commit_session() as session:
        chat = Chat.get_by_telegram_id(message.chat.id)
        bot.send_message(chat.telegram_id, BOT_HELP, disable_web_page_preview=True)


@bot.message_handler(content_types=['photo'])
def process_photo(message):
    with commit_session() as session:
        chat = Chat.get_by_telegram_id(message.chat.id)
        state_changed = False
        if chat.state != CHAT_STATE_WAIT_IMAGES:
            restart(chat)
            chat.state = CHAT_STATE_WAIT_IMAGES
            state_changed = True
            session.flush()
        if len(message.photo) == 0:
            bot.send_message(chat.telegram_id,
                             BOT_PHOTO_FAILURE,
                             reply_to_message_id=message.message_id)
        photo = message.photo[len(message.photo) - 1]
        photo_info = bot.get_file(photo.file_id)
        image = Image(chat, message)
        try:
            with open(image.path, 'wb') as file:
                content = bot.download_file(photo_info.file_path)
                file.write(content)
            session.add(image)
            if state_changed:
                bot.send_message(chat.telegram_id, BOT_CONTINUE)
        except Exception as e:
            print(str(e))
            bot.send_message(chat.telegram_id,
                             BOT_PHOTO_FAILURE,
                             reply_to_message_id=message.message_id)
            session.delete(image)


@bot.message_handler(commands=['soedini'])
def send_combined_message(message):
    with commit_session() as session:
        chat = Chat.get_by_telegram_id(message.chat.id)
        if chat.state != CHAT_STATE_WAIT_IMAGES:
            bot.send_message(chat.telegram_id, BOT_STATE_FAILURE)
            return
        chat.state = None
        session.flush()
        busy_msg_result = bot.send_message(chat.telegram_id, BOT_BUSY)
        busy_message = Message()
        busy_message.telegram_id = busy_msg_result.message_id
        image_list = session.query(Image).filter(Image.chat_id == chat.id).all()
        combined_image = process.get_combined_image(image_list)
        combined_image_path = combined_image_path_template % chat.id
        combined_image.save(combined_image_path)
        bot.send_photo(chat.telegram_id, open(combined_image_path, 'rb'))
        bot.delete_message(chat.telegram_id, busy_message.telegram_id)
        if os.path.exists(combined_image_path):
            os.remove(combined_image_path)
        restart(chat)


def restart(chat):
    with flush_session() as session:
        if not os.path.isdir(tmp_dir):
            os.makedirs(tmp_dir)
        image_list = session.query(Image).filter(Image.chat_id == chat.id).all()
        for image in image_list:
            if os.path.exists(image.path):
                os.remove(image.path)
            session.delete(image)
        chat.state = None
