from typing import Optional

from django.db import models
from django.db.models import BigIntegerField, DateTimeField, ForeignKey, CharField, IntegerField

DATE_FORMAT_HUMAN = '%Y-%m-%d %H:%I:%S'


class Chat(models.Model):
    class Sources(models.TextChoices):
        START = 'start', 'Start'
        HELP = 'help', 'Help'
        CANCEL = 'cancel', 'Cancel'
        PHOTO = 'photo', 'Photo'
        SOEDINI = 'soedini', 'Soedini'
        CALLBACK = 'callback', 'Callback'
        INLINE = 'inline', 'Inline'

    telegram_id: int = BigIntegerField(null=False, blank=False)
    created_at = DateTimeField(auto_now_add=True, null=False, blank=False)
    last_used_at = DateTimeField(null=True, blank=True)
    source = CharField(max_length=15, choices=Sources.choices, null=True, blank=True)

    @staticmethod
    def get_by_telegram_id(telegram_id: int) -> Optional["Chat"]:
        return Chat.objects.filter(telegram_id__exact=telegram_id).first()

    def __str__(self):
        return 'Chat#%d(TelegramID#%d registered at %s)' % (self.id,
                                                           self.telegram_id,
                                                           self.created_at.strftime(DATE_FORMAT_HUMAN))


class Session(models.Model):
    class States(models.TextChoices):
        STARTED = 'started', 'Started'
        FINISHED = 'finished', 'Finished'
        CANCELED = 'canceled', 'Canceled'

    class Modes(models.TextChoices):
        HORIZONTAL = 'horizontal', 'Горизонтально'
        VERTICAL = 'vertical', 'Вертикально'
        TWO_ROWS = 'two_rows', '2 ряда'
        SQUARE = 'square', 'Квадрат'

    chat = ForeignKey(
        'Chat',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
    started_at = DateTimeField(auto_now_add=True, null=False, blank=False)
    state = CharField(max_length=10, choices=States.choices, default=States.STARTED, null=False, blank=False)
    photo_set_finished_at = DateTimeField(null=True, blank=True)
    canceled_at = DateTimeField(null=True, blank=True)
    mode = CharField(max_length=15, choices=Modes.choices, default=Modes.HORIZONTAL, null=False, blank=False)
    control_telegram_message_id = IntegerField(null=True, blank=True)
    control_telegram_message_sent_at = DateTimeField(null=True, blank=True)
    telegram_photo_file_id = CharField(max_length=255, null=True, blank=True)
    query_token = CharField(max_length=36, null=True, blank=True)

    def __str__(self):
        return "Session#%d(Chat#%s started at %s)" % (self.id,
                                                      self.chat.id,
                                                      self.started_at.strftime(DATE_FORMAT_HUMAN))

    @staticmethod
    def get_last_started_session(chat: Chat) -> "Session":
        return Session.objects.filter(chat=chat, state=Session.States.STARTED).last()

    @staticmethod
    def get_by_id(session_id: int) -> "Session":
        return Session.objects.get(pk=session_id)

    @staticmethod
    def get_by_query_token(query_token: str) -> "Session":
        return Session.objects.filter(query_token=query_token).first()


class ModeLog(models.Model):
    session = ForeignKey(
        'Session',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    selected_at = DateTimeField(auto_now_add=True, null=False, blank=False)
    mode = CharField(max_length=15, choices=Session.Modes.choices, null=False, blank=False)

    def __str__(self):
        return 'ModeLog#%d(Session#%d selected_at %s)' % (self.id,
                                                          self.session.id,
                                                          self.selected_at.strftime(DATE_FORMAT_HUMAN))


class Photo(models.Model):
    session = ForeignKey(
        'Session',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
    created_at = DateTimeField(auto_now_add=True, null=False, blank=False)
    telegram_file_id = CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return 'Photo#%d(Session#%d received at %s)' % (self.id,
                                                        self.session.id,
                                                        self.created_at.strftime(DATE_FORMAT_HUMAN))
