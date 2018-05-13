from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import relationship

from .database import flush_session
from .config import tmp_dir


@as_declarative()
class Base(object):
    @declared_attr
    def __tablename__(self):
        return self.__name__.lower()
    id = Column(Integer(), primary_key=True)


CHAT_STATE_WAIT_IMAGES = 'wait_images'


class Chat(Base):
    telegram_id = Column(String(100), index=True, unique=True)
    state = Column(String(100))
    images = relationship('Message', cascade='all, delete-orphan')
    messages = relationship('Message', cascade='all, delete-orphan')

    @staticmethod
    def get_by_telegram_id(telegram_id):
        """
        :rtype: Chat
        :type telegram_id: int
        """
        with flush_session() as session:
            chat = session.query(Chat).filter(Chat.telegram_id == telegram_id).first()
            if chat is None:
                chat = Chat()
                chat.telegram_id = telegram_id
                session.add(chat)
                session.flush()
            return chat


class Message(Base):

    chat_id = Column(Integer, ForeignKey('chat.id'))
    chat = relationship('Chat')
    telegram_id = Column(Integer)


class Image(Base):
    path = Column(String(255))
    chat_id = Column(Integer(), ForeignKey('chat.id'))
    chat = relationship('Chat')

    def __init__(self, chat, message):
        self.chat_id = chat.id
        self.path = tmp_dir + '/image_%d_%d.jpg' % (chat.id, message.message_id)
