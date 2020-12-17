import logging

from telebot import TeleBot, logger

from settings import bot_config

bot = TeleBot(bot_config['token'], threaded=False)

# todo перенети куда-то
logger.setLevel(logging.DEBUG)
