from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import List, Union


class Message:
    """ Common message class """

    def __init__(self, id: str = None,
                 user_id: Union[int, str] = None,
                 timestamp: datetime = None,
                 context: str = None,
                 im_type: str = None,
                 reply_to_id: str = None,
                 buttons: list = None,
                 inline_buttons: list = None):
        self.id = id
        self.user_id = user_id
        self.timestamp = timestamp

        self.context = context
        self.im_type = im_type
        self.reply_to_id = reply_to_id

        self.buttons = buttons
        self.inline_buttons = inline_buttons

    def __str__(self) -> str:
        return (f'{self.__class__.__name__}(id={self.id}, '
                f'im_type={self.im_type}, user={self.user_id})')

    def __add__(self, other) -> MessageList:
        return MessageList(self, other)


class Text(Message):
    """ Simple text message """

    def __init__(self, text: str, **kwargs):
        super().__init__(**kwargs)

        self.text = text


class Contact(Message):
    """ Contact message """

    def __init__(self, contact: dict, text: str = None, **kwargs):
        super().__init__(**kwargs)

        self.contact = contact
        self.text = text


class Location(Message):
    """ Location message """

    def __init__(self, location: Union[tuple, dict, str],
                 text: str = None, **kwargs):
        super().__init__(**kwargs)

        self.location = location
        self.text = text


class RichMedia(Message):
    """ Rich Media message """

    def __init__(self, rich_media: Union[dict, str],
                 text: str = None, **kwargs):
        super().__init__(**kwargs)

        self.rich_media = rich_media
        self.text = text


class Url(Message):
    """ URL message """

    def __init__(self, url: str, text: str = None, **kwargs):
        super().__init__(**kwargs)

        self.url = url
        self.text = text


class Button(Message):
    """ Button message """

    def __init__(self, command: str, text: str = None, **kwargs):
        super().__init__(**kwargs)

        self.command = command
        self.text = text


class File(Message):
    """ File message """

    def __init__(self, file_id: Union[int, str] = None,
                 file_url: str = None,
                 file_size: int = None,
                 file_name: str = None,
                 file_mime_type: str = None,
                 text: str = None, **kwargs):
        super().__init__(**kwargs)

        self.file_id = file_id
        self.file_url = file_url
        self.file_size = file_size
        self.file_name = file_name
        self.file_mime_type = file_mime_type
        self.text = text


class Picture(Message):
    """ Picture message """

    def __init__(self, file_id: Union[int, str] = None,
                 file_url: str = None,
                 file_size: int = None,
                 file_name: str = None,
                 file_mime_type: str = None,
                 text: str = None, **kwargs):
        super().__init__(**kwargs)

        self.file_id = file_id
        self.file_url = file_url
        self.file_size = file_size
        self.file_name = file_name
        self.file_mime_type = file_mime_type
        self.text = text


class Sticker(Message):
    """ Sticker message """

    def __init__(self, file_id: Union[int, str] = None,
                 file_url: str = None,
                 file_size: int = None,
                 file_name: str = None,
                 file_mime_type: str = None,
                 text: str = None, **kwargs):
        super().__init__(**kwargs)

        self.file_id = file_id
        self.file_url = file_url
        self.file_size = file_size
        self.file_name = file_name
        self.file_mime_type = file_mime_type
        self.text = text


class Audio(Message):
    """ Audio message """

    def __init__(self, file_id: Union[int, str] = None,
                 file_url: str = None,
                 file_size: int = None,
                 file_name: str = None,
                 file_mime_type: str = None,
                 file_duration: int = None,
                 is_voice: bool = False,
                 text: str = None, **kwargs):
        super().__init__(**kwargs)

        self.file_id = file_id
        self.file_url = file_url
        self.file_size = file_size
        self.file_name = file_name
        self.file_mime_type = file_mime_type
        self.file_duration = file_duration
        self.is_voice = is_voice
        self.text = text


class Video(Message):
    """ Video message """

    def __init__(self, file_id: Union[int, str] = None,
                 file_url: str = None,
                 file_size: int = None,
                 file_name: str = None,
                 file_mime_type: str = None,
                 file_duration: int = None,
                 is_video_note: bool = False,
                 text: str = None, **kwargs):
        super().__init__(**kwargs)

        self.file_id = file_id
        self.file_url = file_url
        self.file_size = file_size
        self.file_name = file_name
        self.file_mime_type = file_mime_type
        self.file_duration = file_duration
        self.is_video_note = is_video_note
        self.text = text


class EType:
    START = 'start'
    SUBSCRIBED = 'subscribed'
    UNSUBSCRIBED = 'unsubscribed'
    DELIVERED = 'delivered'
    SEEN = 'seen'
    WEBHOOK = 'webhook'
    FAILED = 'failed'
    UNDEFINED = 'undefined'


class Event(Message):
    """ Event message """
    event_type: str = None
    user_name: str = None

    def __init__(self, event_type: str = None,
                 user_name: str = None, **kwargs):
        super().__init__(**kwargs)

        self.event_type = event_type
        self.user_name = user_name


class MessageList(Message):
    """ List of messages """
    message_list: List[Message] = []

    def __init__(self, *messages: Union[Message, MessageList], **kwargs):
        super().__init__(**kwargs)

        for message in messages:
            if isinstance(message, MessageList):
                self.message_list += message.as_list()
            else:
                self.message_list.append(message)
            self.im_type = message.im_type or self.im_type
            self.buttons = message.buttons or self.buttons

    def as_list(self) -> List[Message]:
        return self.message_list
