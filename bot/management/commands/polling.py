from django.core.management import BaseCommand

from bot_lib.bot import bot


class Command(BaseCommand):
    def handle(self, *args, **options):
        bot.polling(none_stop=True, timeout=9999)
