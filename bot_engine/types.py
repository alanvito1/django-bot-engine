from __future__ import annotations


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
        return f'Message(type={self.type}, id={self.id}, ' \
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
        return Message.multiple()

    ##############################################
    # Class methods returning a new typed object #
    ##############################################

    @classmethod
    def start(cls, context: str = None):
        return cls(MessageType.START, context=context)

    @classmethod
    def subscribed(cls, context: str = None):
        return cls(MessageType.SUBSCRIBED, context=context)

    @classmethod
    def unsubscribed(cls, context: str = None):
        return cls(MessageType.UNSUBSCRIBED, context=context)

    @classmethod
    def delivered(cls, message_id: str):
        return cls(MessageType.DELIVERED, message_id=message_id)

    @classmethod
    def seen(cls, message_id: str):
        return cls(MessageType.SEEN, message_id=message_id)

    @classmethod
    def webhook(cls):
        return cls(MessageType.WEBHOOK)

    @classmethod
    def failed(cls, text: str = None):
        return cls(MessageType.FAILED, text=text)

    @classmethod
    def undefined(cls, text: str = None):
        return cls(MessageType.UNDEFINED, text=text)

    @classmethod
    def text(cls, message_id: str,
             user_id: str,
             im_type: str,
             timestamp: int,
             text: str,
             reply_id: str = None):
        return cls(MessageType.TEXT, message_id=message_id, user_id=user_id,
                   im_type=im_type, timestamp=timestamp, text=text)

    @classmethod
    def sticker(cls):
        return cls(MessageType.STICKER)

    @classmethod
    def picture(cls):
        return cls(MessageType.PICTURE)

    @classmethod
    def audio(cls):
        return cls(MessageType.AUDIO)

    @classmethod
    def video(cls):
        return cls(MessageType.VIDEO)

    @classmethod
    def file(cls):
        return cls(MessageType.FILE)

    @classmethod
    def contact(cls):
        return cls(MessageType.CONTACT)

    @classmethod
    def url(cls):
        return cls(MessageType.URL)

    @classmethod
    def location(cls):
        return cls(MessageType.LOCATION)

    @classmethod
    def richmedia(cls):
        return cls(MessageType.RICHMEDIA)

    @classmethod
    def button(cls):
        return cls(MessageType.BUTTON)

    @classmethod
    def keyboard(cls, buttons: list):
        return cls(MessageType.KEYBOARD, buttons=buttons)

    @classmethod
    def multiple(cls, *messages):
        # TODO Check messages
        return cls(MessageType.MULTIPLE, messages=messages)
