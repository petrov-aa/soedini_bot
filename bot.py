from soedini.bot import bot
from soedini.config import bot_config

if __name__ == '__main__':

    if bot_config['update_method'] == 'getUpdates':

        bot.polling(none_stop=True, timeout=9999)
