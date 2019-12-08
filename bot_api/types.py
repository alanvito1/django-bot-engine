from typing import Tuple


class Button:
    """
    Button class
    """

    def __init__(self,
                 text: str, cmd: str,
                 image: str = None, size: Tuple[int, int] = None):
        self.text = text
        self.cmd = 'BTN_' + cmd
        self.image = image
        self.size = size or (2, 1)


class Message:
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
    RICHMEDIA = 'rich_media'  # TODO: need this type?
    KEYBOARD = 'keyboard'  # TODO: need this type?

    service_types = (
        START, SUBSCRIBED, UNSUBSCRIBED,
        DELIVERED, SEEN, WEBHOOK, FAILED, UNDEFINED)
    common_types = (
        TEXT, STICKER, PICTURE, AUDIO, VIDEO, FILE,
        CONTACT, URL, LOCATION, RICHMEDIA, KEYBOARD)

    def __init__(self, message_type: str, message_id: str = None,
                 user_id: str = None, date: int = None, **kwargs):
        self.type = message_type
        self.id = message_id
        self.user_id = user_id
        self.date = date
        self.kwargs = kwargs
        # TODO: add messenger id and type

    @classmethod
    def from_type(cls, message_type, **kwargs):
        message_class = {
            cls.START: StartMessage,
            cls.SUBSCRIBED: SubscribedMessage,
            cls.UNSUBSCRIBED: UnsubscribedMessage,
            cls.DELIVERED: DeliveredMessage,
            cls.SEEN: SeenMessage,
            cls.WEBHOOK: WebhookMessage,
            cls.FAILED: FailedMessage,
            cls.UNDEFINED: Message,
            cls.TEXT: TextMessage,
            cls.STICKER: StickerMessage,
            cls.PICTURE: PictureMessage,
            cls.AUDIO: AudioMessage,
            cls.VIDEO: VideoMessage,
            cls.FILE: FileMessage,
            cls.URL: URLMessage,
            cls.LOCATION: LocationMessage,
            cls.RICHMEDIA: RichMediaMessage,
            cls.KEYBOARD: KeyboardMessage, }
        return message_class[message_type](message_type=message_type, **kwargs)

    def __str__(self):
        return 'msg_id={}, user={}, timestamp={}'.format(
            self.id, self.user_id, self.date)

    @property
    def is_common(self) -> bool:
        return self.type in self.common_types

    @property
    def is_service(self) -> bool:
        return self.type in self.service_types


class TextMessage(Message):
    """"""
    def __init__(self, text: str, **kwargs):
        super().__init__(**kwargs)

        self.text = text


class PictureMessage(Message):
    """"""


class StickerMessage(Message):
    """"""


class AudioMessage(Message):
    """"""


class VideoMessage(Message):
    """"""


class FileMessage(Message):
    """"""


class ContactMessage(Message):
    """"""


class URLMessage(Message):
    """"""


class LocationMessage(Message):
    """"""


class RichMediaMessage(Message):
    """"""


class KeyboardMessage(Message):
    """"""


class StartMessage(Message):
    """"""
    def __init__(self, user_name: str = None, context: str = None, **kwargs):
        super().__init__(**kwargs)

        self.user_name = user_name
        self.context = context


class SubscribedMessage(Message):
    """"""
    def __init__(self, user_name: str = None, context: str = None, **kwargs):
        super().__init__(**kwargs)

        self.user_name = user_name
        self.context = context


class UnsubscribedMessage(Message):
    """"""


class DeliveredMessage(Message):
    """"""


class SeenMessage(Message):
    """"""


class WebhookMessage(Message):
    """"""


class FailedMessage(Message):
    """"""
    def __init__(self, description: str = None, **kwargs):
        super().__init__(**kwargs)

        self.description = description
