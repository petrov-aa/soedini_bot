import shutil

import os
import requests
from telebot import TeleBot, apihelper

from soedini import process
from .database import database
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

if bot_config['use_proxy']:
    apihelper.proxy = proxy_urls


@bot.message_handler(commands=['start', 'cancel'])
def send_start(message):
    session = database.get_session()
    chat = Chat.get_by_telegram_id(message.chat.id)
    restart(chat)
    bot.send_message(chat.telegram_id, BOT_START)
    session.commit()
    session.close()


@bot.message_handler(commands=['help'])
def send_start(message):
    session = database.get_session()
    chat = Chat.get_by_telegram_id(message.chat.id)
    bot.send_message(chat.telegram_id, BOT_HELP)
    session.commit()
    session.close()


@bot.message_handler(content_types=['photo'])
def process_photo(message):
    session = database.get_session()
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
        fetch_telegram_file(photo_info, image.path)
        session.add(image)
        session.flush()
        if state_changed:
            bot.send_message(chat.telegram_id, BOT_CONTINUE)
    except FileNotFoundError:
        bot.send_message(chat.telegram_id,
                         BOT_PHOTO_FAILURE,
                         reply_to_message_id=message.message_id)
        session.delete(image)
        session.flush()
    session.commit()
    session.close()


@bot.message_handler(commands=['soedini'])
def send_combined_message(message):
    session = database.get_session()
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
    bot.send_photo(chat.telegram_id, open(combined_image_path, 'rb'), reply_to_message_id=message.message_id)
    bot.delete_message(chat.telegram_id, busy_message.telegram_id)
    session.commit()
    session.close()


def fetch_telegram_file(file_info, target_path):
    file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(bot_config['token'], file_info.file_path),
                        proxies=proxy_urls,
                        stream=True)
    if file.status_code != 200:
        raise FileNotFoundError('Ошибка загрузки')
    target_dir = os.path.dirname(target_path)
    if not os.path.isdir(target_dir):
        os.makedirs(target_dir)
    with open(target_path, 'wb') as f:
        shutil.copyfileobj(file.raw, f)


def restart(chat):
    session = database.get_session()
    if not os.path.isdir(tmp_dir):
        os.makedirs(tmp_dir)
    image_list = session.query(Image).filter(Image.chat_id == chat.id).all()
    for image in image_list:
        if os.path.exists(image.path):
            os.remove(image.path)
        session.delete(image)
    chat.state = None
    session.flush()
