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
        self.user_id = user_id
        self.timestamp = timestamp
        self.im_type = im_type

        self.user_name = None
        self.context = None
        self.text = None
        self.alt_text = None
        self.sticker_id = None
        self.rich_media = None
        self.file_url = None
        self.file_size = None
        self.file_name = None
        self.url = None
        self.location = None
        self.contact = None
        self.buttons = None

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

    # TODO recheck
    @classmethod
    def text(cls, text: str,
             user_id: str = None, message_id: str = None, **kwargs):
        return cls(MessageType.TEXT,
                   user_id=user_id, message_id=message_id, text=text, **kwargs)

    @classmethod
    def sticker(cls, sticker_id: int,
                user_id: str = None, message_id: str = None, **kwargs):
        return cls(MessageType.STICKER,
                   user_id=user_id, message_id=message_id, sticker_id=sticker_id, **kwargs)

    @classmethod
    def picture(cls, file_url: str, file_size: int = None, file_name: str = None,
                user_id: str = None, message_id: str = None, **kwargs):
        return cls(MessageType.PICTURE,file_url=file_url,
                   file_size=file_size, file_name=file_name,
                   user_id=user_id, message_id=message_id, **kwargs)

    @classmethod
    def audio(cls, file_url: str, file_size: int = None, file_name: str = None,
              user_id: str = None, message_id: str = None, **kwargs):
        return cls(MessageType.AUDIO, file_url=file_url,
                   file_size=file_size, file_name=file_name,
                   user_id=user_id, message_id=message_id, **kwargs)

    @classmethod
    def video(cls, file_url: str, file_size: int = None, file_name: str = None,
              user_id: str = None, message_id: str = None, **kwargs):
        return cls(MessageType.VIDEO, file_url=file_url,
                   file_size=file_size, file_name=file_name,
                   user_id=user_id, message_id=message_id, **kwargs)

    @classmethod
    def file(cls, file_url: str, file_size: int = None, file_name: str = None,
             user_id: str = None, message_id: str = None, **kwargs):
        return cls(MessageType.FILE, file_url=file_url,
                   file_size=file_size, file_name=file_name,
                   user_id=user_id, message_id=message_id, **kwargs)

    @classmethod
    def contact(cls, contact: dict,
                user_id: str = None, message_id: str = None, **kwargs):
        return cls(MessageType.CONTACT, contact=contact,
                   user_id=user_id, message_id=message_id, **kwargs)

    @classmethod
    def url(cls, url: str,
            user_id: str = None, message_id: str = None, **kwargs):
        return cls(MessageType.URL, url=url,
                   user_id=user_id, message_id=message_id, **kwargs)

    @classmethod
    def location(cls, location: dict,
                 user_id: str = None, message_id: str = None, **kwargs):
        return cls(MessageType.LOCATION, location=location,
                   user_id=user_id, message_id=message_id, **kwargs)

    @classmethod
    def richmedia(cls, rich_media: Union[str, dict],
                  user_id: str = None, message_id: str = None, **kwargs):
        return cls(MessageType.RICHMEDIA, rich_media=rich_media,
                   user_id=user_id, message_id=message_id, **kwargs)

    @classmethod
    def button(cls, text: str, command: str = None,
               user_id: str = None, message_id: str = None, **kwargs):
        return cls(MessageType.BUTTON, text=text, command=command,
                   user_id=user_id, message_id=message_id, **kwargs)

    @classmethod
    def keyboard(cls, buttons: List[Union[Message, Model]],
                 user_id: str = None, message_id: str = None, **kwargs):
        return cls(MessageType.KEYBOARD,
                   user_id=user_id, message_id=message_id, buttons=buttons, **kwargs)

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

        return self.messages


# TODO make simple Button class
