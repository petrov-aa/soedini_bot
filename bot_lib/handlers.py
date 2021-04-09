import io
from datetime import datetime
from io import BytesIO

import PIL.Image
import emoji
from telebot import types as tg

from bot.models import Chat, Session
from bot_lib import bot_backend, process
import image_cache
from bot_lib.bot import bot
from bot_messages.messages import t

CALLBACK_ACTION_CHANGE_MODE = 'm'
CALLBACK_BUTTON_DATA_DELIMITER = ':'
CALLBACK_ACTIONS = [
    CALLBACK_ACTION_CHANGE_MODE,
]
PHOTO_PIL_FORMAT = 'JPEG'


@bot.message_handler(commands=['start'])
def on_start_command(message: tg.Message):
    telegram_chat_id = message.chat.id
    chat = bot_backend.get_chat_by_telegram_id(telegram_chat_id, True, Chat.Sources.START)
    bot.send_message(chat.telegram_id, t('bot.messages.start'))


@bot.message_handler(commands=['help'])
def on_help_command(message: tg.Message):
    telegram_chat_id = message.chat.id
    chat = bot_backend.get_chat_by_telegram_id(telegram_chat_id, True, Chat.Sources.HELP)
    bot.send_message(chat.telegram_id, t('bot.messages.start'))


# todo Разделить эти команды по языку
@bot.message_handler(commands=['soedini', 'join'])
def on_soedini_command(message: tg.Message):
    telegram_chat_id = message.chat.id
    chat = bot_backend.get_chat_by_telegram_id(telegram_chat_id, True, Chat.Sources.SOEDINI)
    if not bot_backend.chat_has_active_session(chat):
        bot.send_message(chat.telegram_id, t('bot.state.error'))
        return
    session = bot_backend.get_active_session(chat)
    photos = session.photo_set.all()
    if len(photos) == 0:
        bot.send_message(chat.telegram_id, t('bot.state.error'))
        return
    bot_backend.finish_session(session)
    bot_backend.push_history_item(session)
    send_combined_image(session)


@bot.message_handler(commands=['cancel'])
def on_cancel_command(message):
    telegram_chat_id = message.chat.id
    chat = bot_backend.get_chat_by_telegram_id(telegram_chat_id, True, Chat.Sources.CANCEL)
    if bot_backend.chat_has_active_session(chat):
        session = bot_backend.get_active_session(chat)
        bot_backend.cancel_session(session)
    bot.send_message(telegram_chat_id, t('bot.messages.cancel'))


@bot.message_handler(content_types=['photo'])
def on_photo_message(message: tg.Message):
    telegram_chat_id = message.chat.id
    if len(message.photo) == 0:
        return
    file_id = message.photo[-1].file_id
    chat = bot_backend.get_chat_by_telegram_id(telegram_chat_id, True, Chat.Sources.PHOTO)
    new_session_created = False
    if not bot_backend.chat_has_active_session(chat):
        active_session = bot_backend.create_session(chat)
        new_session_created = True
    else:
        active_session = bot_backend.get_active_session(chat)
    bot_backend.add_photo_to_session(active_session, file_id)
    if new_session_created:
        bot.send_message(chat.telegram_id, t('bot.messages.continue'))


@bot.callback_query_handler(lambda query: True)
def on_callback_query(query: tg.CallbackQuery):
    query_id = query.id
    telegram_user_id = query.from_user.id
    chat = bot_backend.get_chat_by_telegram_id(telegram_user_id, True, Chat.Sources.CALLBACK)
    data = parse_get_mode_control_button_data(query.data)
    if data[0] not in CALLBACK_ACTIONS:
        bot.answer_callback_query(query_id, t('bot.callback.error'))
        return
    session_id = int(data[1])
    session = bot_backend.get_session_by_id(session_id)
    if session is None:
        bot.answer_callback_query(query_id, t('bot.callback.error'))
        return
    if session.chat.id != chat.id:
        bot.answer_callback_query(query_id, t('bot.callback.error'))
        return
    if data[0] == CALLBACK_ACTION_CHANGE_MODE:
        mode = data[2]
        if mode not in [Session.Modes.HORIZONTAL, Session.Modes.VERTICAL, Session.Modes.TWO_ROWS, Session.Modes.SQUARE]:
            mode = Session.Modes.HORIZONTAL
        bot_backend.change_mode(session, mode)
        bot_backend.push_history_item(session)
    send_combined_image(session)


@bot.inline_handler(lambda query: True)
def on_inline_query(query: tg.InlineQuery):
    telegram_user_id = query.from_user.id
    query_id = query.id
    query = query.query
    if len(query) == 0:
        txt = t('bot.inline.switch_pm_text')
        bot.answer_inline_query(query_id,
                                [],
                                switch_pm_text=txt,
                                switch_pm_parameter='start')
        return
    try:
        session = Session.get_by_query_token(query)
    except:
        bot.answer_inline_query(query_id,
                                [],
                                switch_pm_text=t('bot.inline.switch_pm_text'),
                                switch_pm_parameter='start')
        return
    if session is None or session.chat.telegram_id != telegram_user_id:
        bot.answer_inline_query(query_id,
                                [],
                                switch_pm_text=t('bot.inline.switch_pm_text'),
                                switch_pm_parameter='start')
        return
    photo = tg.InlineQueryResultCachedPhoto('%s - %s' % (str(session.id), str(query_id)),
                                            session.telegram_photo_file_id)
    bot.answer_inline_query(query_id, results=[photo])


def get_control_button_caption(mode_str: str, is_active: bool):
    if not is_active:
        return mode_str
    return emoji.emojize(t('bot.buttons.mode.title', mode=mode_str))


def get_mode_control_button_data(session_id: int, mode: str):
    return CALLBACK_BUTTON_DATA_DELIMITER.join(
        (CALLBACK_ACTION_CHANGE_MODE, str(session_id), mode)
    )


def parse_get_mode_control_button_data(data: str):
    return tuple(data.split(CALLBACK_BUTTON_DATA_DELIMITER, 2))


def get_mode_control_button(mode_user_title: str, mode: str, session_id: int, is_active: bool):
    caption = get_control_button_caption(emoji.emojize(mode_user_title, use_aliases=True), is_active)
    data = get_mode_control_button_data(session_id, mode)
    return tg.InlineKeyboardButton(caption, callback_data=data)


def get_control_markup(session: Session, images_count: int) -> tg.InlineKeyboardMarkup:
    markup = tg.InlineKeyboardMarkup(row_width=4)
    mode_is_horizontal = session.mode == Session.Modes.HORIZONTAL
    mode_is_vertical = session.mode == Session.Modes.VERTICAL
    mode_is_two_rows = session.mode == Session.Modes.TWO_ROWS
    # mode_is_square = session.mode == Session.Modes.SQUARE
    button_h = get_mode_control_button(Session.Modes.HORIZONTAL.label,
                                       Session.Modes.HORIZONTAL,
                                       session.id,
                                       mode_is_horizontal)
    button_v = get_mode_control_button(Session.Modes.VERTICAL.label,
                                       Session.Modes.VERTICAL,
                                       session.id,
                                       mode_is_vertical)
    markup.row(button_h)
    markup.row(button_v)
    if images_count > 2:
        button_2r = get_mode_control_button(Session.Modes.TWO_ROWS.label,
                                            Session.Modes.TWO_ROWS,
                                            session.id,
                                            mode_is_two_rows)
        # button_s = get_mode_control_button(Session.Modes.SQUARE.label,
        #                                    Session.Modes.SQUARE,
        #                                    session.id,
        #                                    mode_is_square)
        markup.row(button_2r)
    inline_query = session.query_token
    button_send = tg.InlineKeyboardButton(t('bot.buttons.send'), switch_inline_query=inline_query)
    markup.add(button_send)
    return markup


def send_combined_image(session: Session):
    photos = session.photo_set.all()
    images = list()
    for photo in photos:
        image_content = image_cache.get_image(str(photo.id))
        if image_content is None:
            photo_file_info = bot.get_file(photo.telegram_file_id)
            image_content = bot.download_file(photo_file_info.file_path)
            image_cache.store_image(str(photo.id), image_content)
        image_bytes = io.BytesIO(image_content)
        image = PIL.Image.open(image_bytes)
        images.append(image)
    combined_image = process.get_combined_image(images, session.mode)
    combined_image_bytes_stream = BytesIO()
    combined_image.save(combined_image_bytes_stream, format=PHOTO_PIL_FORMAT)
    combined_image_bytes_stream.flush()
    combined_image_bytes_stream.seek(0)
    bot_backend.update_session_query_token(session)
    if session.control_telegram_message_id is not None:
        message = bot.edit_message_media(tg.InputMediaPhoto(combined_image_bytes_stream.getvalue()),
                                         session.chat.telegram_id,
                                         session.control_telegram_message_id,
                                         reply_markup=get_control_markup(session, len(photos)))
    else:
        message = bot.send_photo(session.chat.telegram_id,
                                 combined_image_bytes_stream.getvalue(),
                                 reply_markup=get_control_markup(session, len(photos)))
    bot_backend.set_session_telegram_message_id(session, message.message_id, datetime.fromtimestamp(message.date))
    bot_backend.set_session_combined_photo_file_id(session, message.photo[-1].file_id)
