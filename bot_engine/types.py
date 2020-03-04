from __future__ import annotations
from typing import List, Union

from django.db.models import Model


class MessageType:
    # Service types
    START = 'start'
    SUBSCRIBED = 'subscribed'
    UNSUBSCRIBED = 'unsubscribed'
    DELIVERED = 'delivered'
    SEEN = 'seen'
    WEBHOOK = 'webhook'
    FAILED = 'failed'
    UNDEFINED = 'undefined'
    # Common types
    TEXT = 'text'
    STICKER = 'sticker'
    PICTURE = 'picture'
    AUDIO = 'audio'
    VIDEO = 'video'
    FILE = 'file'
    CONTACT = 'contact'
    URL = 'url'
    LOCATION = 'location'
    RICHMEDIA = 'richmedia'
    BUTTON = 'button'
    KEYBOARD = 'keyboard'
    # Combined
    MULTIPLE = 'multiple'

    service_types = (START, SUBSCRIBED, UNSUBSCRIBED, DELIVERED, SEEN,
                     WEBHOOK, FAILED, UNDEFINED, )
    common_types = (TEXT, STICKER, PICTURE, AUDIO, VIDEO, FILE,
                    CONTACT, URL, LOCATION, RICHMEDIA, KEYBOARD, )
    choices = (
        [(msg_type, msg_type.capitalize()) for msg_type in common_types] +
        [(msg_type, msg_type.capitalize()) for msg_type in service_types]
    )


class Message:
    def __init__(self, message_type: str,
                 message_id: str = None,
                 user_id: str = None,
                 im_type: str = None,
                 timestamp: int = None,
                 **kwargs):
        self.type = message_type
        self.id = message_id
        self.im_type = im_type
        self.user_id = user_id
        self.timestamp = timestamp

        for key, value in kwargs.items():
            setattr(self, key, value)

        # self.user_name = kwargs.get('user_name')
        # self.context = kwargs.get('context')
        # self.error = kwargs.get('error')

    def __str__(self) -> str:
        return f'Message({self.type}, id={self.id}, ' \
               f'im_type={self.im_type}, user={self.user_id})'

    def __repr__(self) -> str:
        return f'<bot_engine.Message object ' \
               f'(type={self.type}, im_type={self.im_type})>'

    @property
    def is_common(self) -> bool:
        return self.type in MessageType.common_types

    @property
    def is_service(self) -> bool:
        return self.type in MessageType.service_types

    @property
    def is_text(self) -> bool:
        return self.type in [MessageType.TEXT]

    @property
    def is_button(self) -> bool:
        return self.type in [MessageType.BUTTON]

    def __add__(self, other) -> Message:
        return Message.multiple(self, other)

    ##############################################
    # Class methods returning a new typed object #
    ##############################################

    @classmethod
    def start(cls, user_id: str, message_id: str = None,
              timestamp: int = None, user_name: str = None,
              context: str = None, **kwargs):
        return cls(MessageType.START,
                   user_id=user_id, message_id=message_id,
                   timestamp=timestamp, user_name=user_name,
                   context=context, **kwargs)

    @classmethod
    def subscribed(cls, user_id: str, message_id: str = None,
                   timestamp: int = None, user_name: str = None,
                   context: str = None, **kwargs):
        return cls(MessageType.SUBSCRIBED,
                   user_id=user_id, message_id=message_id,
                   timestamp=timestamp, user_name=user_name,
                   context=context, **kwargs)

    @classmethod
    def unsubscribed(cls, user_id: str, message_id: str = None,
                     timestamp: int = None, **kwargs):
        return cls(MessageType.UNSUBSCRIBED,
                   user_id=user_id, message_id=message_id,
                   timestamp=timestamp, **kwargs)

    @classmethod
    def delivered(cls, user_id: str, message_id: str,
                  timestamp: int = None, **kwargs):
        return cls(MessageType.DELIVERED,
                   user_id=user_id, message_id=message_id,
                   timestamp=timestamp, **kwargs)

    @classmethod
    def seen(cls, user_id: str, message_id: str,
             timestamp: int = None, **kwargs):
        return cls(MessageType.SEEN,
                   user_id=user_id, message_id=message_id,
                   timestamp=timestamp, **kwargs)

    @classmethod
    def webhook(cls, timestamp: int = None, **kwargs):
        return cls(MessageType.WEBHOOK, timestamp=timestamp, **kwargs)

    @classmethod
    def failed(cls, user_id: str, message_id: str,
               timestamp: int = None, text: str = None, **kwargs):
        return cls(MessageType.FAILED,
                   user_id=user_id, message_id=message_id,
                   timestamp=timestamp, text=text, **kwargs)

    @classmethod
    def undefined(cls, user_id: str = None, message_id: str = None,
                  timestamp: int = None, text: str = None, **kwargs):
        return cls(MessageType.UNDEFINED,
                   user_id=user_id, message_id=message_id,
                   timestamp=timestamp, text=text, **kwargs)

    @classmethod
    def text(cls, text: str, **kwargs):
        return cls(MessageType.TEXT, text=text, **kwargs)

    @classmethod
    def sticker(cls, sticker_id: int, **kwargs):
        return cls(MessageType.STICKER, sticker_id=sticker_id, **kwargs)

    @classmethod
    def picture(cls, **kwargs):
        return cls(MessageType.PICTURE, **kwargs)

    @classmethod
    def audio(cls, **kwargs):
        return cls(MessageType.AUDIO, **kwargs)

    @classmethod
    def video(cls, **kwargs):
        return cls(MessageType.VIDEO, **kwargs)

    @classmethod
    def file(cls, **kwargs):
        return cls(MessageType.FILE, **kwargs)

    @classmethod
    def contact(cls, **kwargs):
        return cls(MessageType.CONTACT, **kwargs)

    @classmethod
    def url(cls, **kwargs):
        return cls(MessageType.URL, **kwargs)

    @classmethod
    def location(cls, **kwargs):
        return cls(MessageType.LOCATION, **kwargs)

    @classmethod
    def richmedia(cls, **kwargs):
        return cls(MessageType.RICHMEDIA, **kwargs)

    @classmethod
    def button(cls, **kwargs):
        return cls(MessageType.BUTTON, **kwargs)

    @classmethod
    def keyboard(cls, buttons: List[Union[Message, Model]], **kwargs):
        return cls(MessageType.KEYBOARD, buttons=buttons, **kwargs)

    @classmethod
    def multiple(cls, *messages: Message, **kwargs):
        assert len(messages) > 1, 'You must place more than one message'
        for msg in messages:
            assert (isinstance(msg, Message),
                    'All elements must be bot_engine.Message type')

        im_type = messages[0].im_type

        return cls(MessageType.MULTIPLE, messages=messages,
                   im_type=im_type, **kwargs)

    def as_list(self) -> List[Message]:
        assert self.type == MessageType.MULTIPLE, ''


# TODO make simple Button class
