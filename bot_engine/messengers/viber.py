import json
import logging
from typing import Any, Dict, List, Optional, Union

from django.contrib.sites.models import Site
from django.db.models import Model
from django.http.request import HttpRequest
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api import messages as vbm
from viberbot.api.messages.message import Message as VbMessage
from viberbot.api.messages.typed_message import TypedMessage
from viberbot.api import viber_requests as vbr
from viberbot.api.viber_requests.viber_request import ViberRequest

from .base_messenger import BaseMessenger
from ..errors import MessengerException, NotSubscribed, RequestsLimitExceeded
from ..types import (
    Message, Text, Contact, Location, RichMedia, Url, Button,
    File, Picture, Sticker, Audio, Video, Event, EType, MessageList
)


log = logging.getLogger(__name__)


class Viber(BaseMessenger):
    """
    IM connector for Viber Bot API
    """
    # region Interface

    def __init__(self, token: str, **kwargs):
        super().__init__(token, **kwargs)

        self.bot = Api(BotConfiguration(
            auth_token=token,
            name=kwargs.get('name'),
            avatar=kwargs.get('avatar'),
        ))

    def enable_webhook(self, url: str, **kwargs):
        return self.bot.set_webhook(url=url)

    def disable_webhook(self):
        return self.bot.unset_webhook()

    def get_account_info(self) -> Dict[str, Any]:
        # data = {
        #    "status":0,
        #    "status_message":"ok",
        #    "id":"pa:75346594275468546724",
        #    "name":"account name",
        #    "uri":"accountUri",
        #    "icon":"http://example.com",
        #    "background":"http://example.com",
        #    "category":"category",
        #    "subcategory":"sub category",
        #    "location":{
        #       "lon":0.1,
        #       "lat":0.2
        #    },
        #    "country":"UK",
        #    "webhook":"https://my.site.com",
        #    "event_types":[
        #       "delivered",
        #       "seen"
        #    ],
        #    "subscribers_count":35,
        #    "members":[
        #       {
        #          "id":"01234567890A=",
        #          "name":"my name",
        #          "avatar":"http://example.com",
        #          "role":"admin"
        #       }
        #    ]
        # }
        try:
            data = self.bot.get_account_info()
        except Exception as err:
            raise MessengerException(err)

        return {
            'id': data.get('id'),
            'username': data.get('name'),
            'uri': data.get('uri'),  # check this
            'info': data
        }

    def get_user_info(self, user_id: str, **kwargs) -> Dict[str, Any]:
        # data = {
        #   "id":"01234567890A=",
        #   "name":"John McClane",
        #   "avatar":"http://avatar.example.com",
        #   "country":"UK",
        #   "language":"en",
        #   "primary_device_os":"android 7.1",
        #   "api_version":1,
        #   "viber_version":"6.5.0",
        #   "mcc":1,
        #   "mnc":1,
        #   "device_type":"iPhone9,4"
        # }
        try:
            data = self.bot.get_user_details(user_id)
        except Exception as err:
            if 'failed with status: 12' in str(err):
                raise RequestsLimitExceeded(err)
            raise MessengerException(err)

        return {
            'id': data.get('id'),
            'username': data.get('name'),
            'avatar': data.get('avatar'),
            'info': data,
        }

    def parse_message(self, request: HttpRequest) -> Message:
        # Verify signature
        sign = request.META.get('HTTP_X_VIBER_CONTENT_SIGNATURE')
        data = json.loads(request.body)
        if not self.bot.verify_signature(request.body, sign):
            raise MessengerException(f'Viber message not verified; '
                                     f'Data={data}; Sign={sign};')

        return self._from_viber_message(self.bot.create_request(data))

    def send_message(self, receiver: str,
                     messages: Union[Message, List[Message]]) -> List[str]:
        if isinstance(messages, MessageList):
            messages = messages.as_list()
        elif isinstance(messages, Message):
            messages = [messages]

        vb_messages = []
        for message in messages:
            vb_messages.append(self._to_viber_message(message))

        try:
            return self.bot.send_messages(receiver, vb_messages)
        except Exception as err:
            if 'failed with status: 6, message: notSubscribed' in str(err):
                raise NotSubscribed(err)
            raise MessengerException(err)

    def welcome_message(self, text: str) -> Union[str, Dict[str, Any], None]:
        return {
            "sender": {
                "name": self.name,
                "avatar": self.avatar_url
            },
            "type": "text",
            "text": text
        }

    # endregion

    # region Help methods

    @staticmethod
    def _from_viber_message(vb_request: ViberRequest) -> Message:
        if isinstance(vb_request, vbr.ViberMessageRequest):
            assert isinstance(vb_request.message, TypedMessage)

            vb_message = vb_request.message
            if isinstance(vb_message, vbm.TextMessage):
                if 'btn-' in vb_message.text:
                    return Button(
                        id=vb_request.message_token, user_id=vb_request.sender.id,
                        timestamp=vb_request.timestamp, command=vb_message.text
                    )
                return Text(
                    id=vb_request.message_token, user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp, text=vb_message.text
                )
            elif isinstance(vb_message, vbm.PictureMessage):
                return Picture(
                    id=vb_request.message_token, user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp, file_url=vb_message.media
                )
            elif isinstance(vb_message, vbm.VideoMessage):
                return Video(
                    id=vb_request.message_token, user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp, file_url=vb_message.media,
                    file_size=vb_message.size
                )
            elif isinstance(vb_message, vbm.FileMessage):
                return File(
                    id=vb_request.message_token, user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp, file_url=vb_message.media,
                    file_size=vb_message.size
                )
            elif isinstance(vb_message, vbm.RichMediaMessage):
                return RichMedia(
                    id=vb_request.message_token, user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp, text=vb_message.alt_text,
                    rich_media=vb_message.rich_media
                )
            elif isinstance(vb_message, vbm.ContactMessage):
                return Contact(
                    id=vb_request.message_token, user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp, contact=vb_message.contact
                )
            elif isinstance(vb_message, vbm.LocationMessage):
                return Location(
                    id=vb_request.message_token, user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp, location=vb_message.location
                )
            elif isinstance(vb_message, vbm.URLMessage):
                return Url(
                    id=vb_request.message_token, user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp, url=vb_message.media
                )
            elif isinstance(vb_message, vbm.StickerMessage):
                return Sticker(
                    id=vb_request.message_token, user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp,
                    file_id=vb_message.sticker_id
                )
            return Text(
                id=vb_request.message_token, user_id=vb_request.sender.id,
                timestamp=vb_request.timestamp, text=str(vb_message)
            )
        elif isinstance(vb_request, vbr.ViberConversationStartedRequest):
            return Event(
                id=vb_request.message_token, user_id=vb_request.user_id,
                timestamp=vb_request.timestamp, event_type=EType.START,
                user_name=vb_request.user.name, context=vb_request.context
            )
        elif isinstance(vb_request, vbr.ViberSubscribedRequest):
            return Event(
                id=vb_request.message_token, user_id=vb_request.user_id,
                timestamp=vb_request.timestamp, event_type=EType.SUBSCRIBED,
                user_name=vb_request.user.name
            )
        elif isinstance(vb_request, vbr.ViberUnsubscribedRequest):
            return Event(
                id=vb_request.message_token, user_id=vb_request.user_id,
                timestamp=vb_request.timestamp, event_type=EType.UNSUBSCRIBED
            )
        elif isinstance(vb_request, vbr.ViberDeliveredRequest):
            return Event(
                id=vb_request.message_token, user_id=vb_request.user_id,
                timestamp=vb_request.timestamp, event_type=EType.DELIVERED
            )
        elif isinstance(vb_request, vbr.ViberSeenRequest):
            return Event(
                id=vb_request.message_token, user_id=vb_request.user_id,
                timestamp=vb_request.timestamp, event_type=EType.SEEN
            )
        elif isinstance(vb_request, vbr.ViberFailedRequest):
            log.warning(f'Client failed receiving message; Error={vb_request}')
            return Event(
                id=vb_request.message_token, user_id=vb_request.user_id,
                timestamp=vb_request.timestamp, event_type=EType.START,
                context=vb_request.desc
            )
        elif vb_request.event_type == 'webhook':
            return Event(timestamp=vb_request.timestamp)

        log.warning(f'ViberRequest type={type(vb_request)}; '
                    f'Object={vb_request};')
        return Text(timestamp=vb_request.timestamp, text=str(vb_request))

    def _to_viber_message(self, message: Message) -> VbMessage:
        kb = self._get_keyboard(message.buttons)

        if isinstance(message, Text):
            return vbm.TextMessage(text=message.text, keyboard=kb)
        if isinstance(message, Sticker):
            return vbm.StickerMessage(sticker_id=message.file_id, keyboard=kb)
        elif isinstance(message, Picture):
            return vbm.PictureMessage(
                media=message.file_url, text=message.text, keyboard=kb
            )
        elif isinstance(message, Video):
            return vbm.VideoMessage(
                media=message.file_url, size=message.file_size,
                text=message.text, keyboard=kb
            )
        elif isinstance(message, (File, Audio)):
            return vbm.FileMessage(
                media=message.file_url, size=message.file_size or 0,
                file_name=message.file_name or '', keyboard=kb
            )
        elif isinstance(message, Contact):
            contact = message.contact
            return vbm.ContactMessage(contact=contact, keyboard=kb)
        elif isinstance(message, Url):
            return vbm.URLMessage(media=message.url, keyboard=kb)
        elif isinstance(message, Location):
            location = message.location
            return vbm.LocationMessage(location=location, keyboard=kb)
        elif isinstance(message, RichMedia):
            rich_media = message.rich_media
            return vbm.RichMediaMessage(
                rich_media=rich_media, alt_text=message.text, keyboard=kb
            )

    @staticmethod
    def _get_keyboard(buttons: List[Button]) -> Optional[Dict[str, Any]]:
        # TODO do refactoring
        if not buttons:
            return None

        vb_buttons = []
        for button in buttons:
            # assert isinstance(button, Button), f'{button=} {type(button)}'
            vb_btn = {
                'Columns': 2,  # TODO: how is it storage in Model?
                'Rows': 1,
                'BgColor': '#aaaaaa',
                'ActionType': 'reply',
                'ActionBody': button.command,
                'Text': '<font color="{clr}"><b>{text}'
                        '</b></font>'.format(text=button.text, clr='#131313'),
                'TextVAlign': 'middle', 'TextHAlign': 'center',
                'TextOpacity': 60, 'TextSize': 'large',
                'TextPaddings': [12, 8, 8, 20],  # [up, left, right, bottom]
            }

            if hasattr(button, 'image'):
                domain = Site.objects.get_current().domain
                vb_btn.update({
                    'BgMedia': f'https://{domain}{button.image}',
                    'BgMediaScaleType': 'fill'
                })

            vb_buttons.append(vb_btn)

        return {
            'Type': 'keyboard',
            'BgColor': '#ffffff',
            'min_api_version': 6,
            'Buttons': vb_buttons,
        }

    # endregion
