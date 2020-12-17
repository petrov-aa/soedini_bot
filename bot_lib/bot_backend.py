import uuid
from datetime import datetime
from typing import Optional

from django.utils import timezone
from django.utils.timezone import now

from bot.models import Chat, Session, Photo, ModeLog


class BotBackendException(Exception):
    pass


class BotBackendLogicException(BotBackendException):
    pass


def get_chat_by_telegram_id(telegram_chat_id: int,
                            update_last_used_at: bool,
                            source: str) -> Chat:
    chat = Chat.get_by_telegram_id(telegram_chat_id)
    if chat is None:
        chat = Chat(telegram_id=telegram_chat_id, last_used_at=now(), source=source)
    if update_last_used_at:
        chat.last_used_at = now()
        chat.save()
    return chat


def chat_has_active_session(chat: Chat) -> bool:
    active_session = Session.get_last_started_session(chat)
    return active_session is not None


def get_active_session(chat: Chat) -> Optional[Session]:
    return Session.get_last_started_session(chat)


def create_session(chat: Chat) -> Session:
    active_session = get_active_session(chat)
    if active_session is not None:
        raise BotBackendLogicException("Chat already has active session.")
    active_session = Session(chat=chat)
    active_session.save()
    return active_session


def get_session_by_id(session_id: int) -> Session:
    return Session.get_by_id(session_id)


def add_photo_to_session(session: Session, telegram_file_id) -> Photo:
    photo = Photo(telegram_file_id=telegram_file_id)
    photo.session = session
    photo.save()
    return photo


def cancel_session(session: Session):
    if session.state == Session.States.CANCELED:
        raise BotBackendLogicException("Session is already canceled.")
    session.state = Session.States.CANCELED
    session.canceled_at = now()
    session.save()


def finish_session(session: Session):
    if session.state == Session.States.FINISHED:
        raise BotBackendLogicException("Session is already finished.")
    session.state = Session.States.FINISHED
    session.photo_set_finished_at = now()
    session.save()


def change_mode(session: Session, mode: str):
    session.mode = mode
    session.save()


def change_output_mode(session: Session, output_mode: str):
    session.output_mode = output_mode
    session.save()


def push_history_item(session: Session):
    history = ModeLog(session=session, mode=session.mode)
    history.save()


def set_session_telegram_message_id(session: Session, telegram_message_id: int, sent_at: datetime):
    session.control_telegram_message_id = telegram_message_id
    session.control_telegram_message_sent_at = timezone.make_aware(sent_at)
    session.save()


def set_session_combined_photo_file_id(session: Session, file_id: str):
    session.telegram_photo_file_id = file_id
    session.save()


def update_session_query_token(session: Session):
    session.query_token = str(uuid.uuid4())
    session.save()
