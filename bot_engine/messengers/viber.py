import logging
from typing import Any, Dict, List, Union

from django.contrib.sites.models import Site
from django.db.models import Model
from django.utils import timezone
from rest_framework.request import Request
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api import messages as v_messages
from viberbot.api.messages.message import Message as VbMessage
from viberbot.api.messages.typed_message import TypedMessage
from viberbot.api import viber_requests as v_requests
from viberbot.api.viber_requests.viber_request import ViberRequest

from .base_messenger import BaseMessenger
from ..errors import MessengerException, NotSubscribed, RequestsLimitExceeded
from ..types import Message, MessageType


log = logging.getLogger(__name__)


class Viber(BaseMessenger):
    """
    IM connector for Viber REST API
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

    def parse_message(self, request: Request) -> Message:
        # NOTE: There is no way to get the body
        #       after processing the request in DRF.
        # # Verify signature
        # sign = request.META.get('HTTP_X_VIBER_CONTENT_SIGNATURE')
        # if not self.bot.verify_signature(request.body, sign):
        #     raise IMApiException(f'Viber message not verified; '
        #                          f'Data={request.data}; Sign={sign};')

        vb_request = v_requests.create_request(request.data)

        return self._from_viber_message(vb_request)

    def send_message(self, receiver: str,
                     messages: Union[Message, List[Message]]) -> List[str]:
        vb_messages = []

        if isinstance(messages, Message):
            if messages.type == MessageType.MULTIPLE:
                messages = messages.as_list()
            else:
                messages = [messages]

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
        log.debug(f'vb_request={vb_request}')

        if isinstance(vb_request, v_requests.ViberMessageRequest):
            vb_message = vb_request.message
            log.debug(f'vb_message={vb_message}')

            assert isinstance(vb_message, TypedMessage)

            if isinstance(vb_message, v_messages.TextMessage):
                msg_type = MessageType.TEXT
                if 'btn-' in vb_message.text:
                    msg_type = MessageType.BUTTON
                return Message(
                    message_type=msg_type,
                    message_id=vb_request.message_token,
                    user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp,
                    text=vb_message.text)
            elif isinstance(vb_message, v_messages.PictureMessage):
                return Message.picture(
                    message_id=vb_request.message_token,
                    user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp,
                    file_url=vb_message.media)
            elif isinstance(vb_message, v_messages.VideoMessage):
                return Message.video(
                    message_id=vb_request.message_token,
                    user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp,
                    file_url=vb_message.media,
                    file_size=vb_message.size)
            elif isinstance(vb_message, v_messages.FileMessage):
                return Message.file(
                    message_id=vb_request.message_token,
                    user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp,
                    file_url=vb_message.media,
                    file_size=vb_message.size)
            elif isinstance(vb_message, v_messages.RichMediaMessage):
                return Message.richmedia(
                    message_id=vb_request.message_token,
                    user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp,
                    rich_media=vb_message.rich_media,
                    alt_text=vb_message.alt_text)
            elif isinstance(vb_message, v_messages.URLMessage):
                return Message.url(
                    message_id=vb_request.message_token,
                    user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp,
                    url=vb_message.media)
            elif isinstance(vb_message, v_messages.LocationMessage):
                return Message.location(
                    message_id=vb_request.message_token,
                    user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp,
                    location=vb_message.location)
            elif isinstance(vb_message, v_messages.ContactMessage):
                return Message.contact(
                    message_id=vb_request.message_token,
                    user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp,
                    contact=vb_message.contact)
            elif isinstance(vb_message, v_messages.StickerMessage):
                return Message.sticker(
                    message_id=vb_request.message_token,
                    user_id=vb_request.sender.id,
                    timestamp=vb_request.timestamp,
                    sticker_id=vb_message.sticker_id)
            return Message.undefined(
                message_id=vb_request.message_token,
                user_id=vb_request.sender.id,
                timestamp=vb_request.timestamp,
                text=str(vb_message))
        elif isinstance(vb_request, v_requests.ViberConversationStartedRequest):
            return Message.start(
                user_id=vb_request.user.id,
                timestamp=vb_request.timestamp,
                message_id=vb_request.message_token,
                user_name=vb_request.user.name,
                context=vb_request.context)
        elif isinstance(vb_request, v_requests.ViberSubscribedRequest):
            return Message.subscribed(
                user_id=vb_request.user.id,
                timestamp=vb_request.timestamp,
                user_name=vb_request.user.name)
        elif isinstance(vb_request, v_requests.ViberUnsubscribedRequest):
            return Message.unsubscribed(
                user_id=vb_request.user_id,
                timestamp=vb_request.timestamp)
        elif isinstance(vb_request, v_requests.ViberDeliveredRequest):
            return Message.delivered(
                user_id=vb_request.user_id,
                message_id=vb_request.meesage_token,
                timestamp=vb_request.timestamp)
        elif isinstance(vb_request, v_requests.ViberSeenRequest):
            return Message.seen(
                user_id=vb_request.user_id,
                message_id=vb_request.meesage_token,
                timestamp=vb_request.timestamp)
        elif isinstance(vb_request, v_requests.ViberFailedRequest):
            log.warning(f'Client failed receiving message; Error={vb_request}')
            return Message.failed(
                user_id=vb_request.user_id,
                message_id=vb_request.meesage_token,
                timestamp=timezone.now().timestamp(),
                text=vb_request.desc)
        elif vb_request.event_type == 'webhook':
            return Message.webhook(timestamp=vb_request.timestamp)

        log.warning(f'ViberRequest type={type(vb_request)}; '
                    f'Object={vb_request};')
        return Message.undefined(
            timestamp=vb_request.timestamp,
            text=str(vb_request))

    def _to_viber_message(self, message: Message) -> VbMessage:
        if message.buttons:
            kb = self._get_keyboard(message.buttons)
        else:
            kb = None

        # TODO recheck and finish all types
        if message.type == MessageType.TEXT:
            return v_messages.TextMessage(text=message.text, keyboard=kb)
        if message.type == MessageType.STICKER:
            return v_messages.StickerMessage(sticker_id=message.sticker_id,
                                             keyboard=kb)
        elif message.type == MessageType.PICTURE:
            return v_messages.PictureMessage(media=message.file_url,
                                             text=message.text,
                                             keyboard=kb)
        elif message.type == MessageType.VIDEO:
            return v_messages.VideoMessage(media=message.file_url,
                                           size=message.file_size,
                                           text=message.text,
                                           keyboard=kb)
        elif message.type in [MessageType.FILE, MessageType.AUDIO]:
            return v_messages.FileMessage(media=message.file_url,
                                          size=message.file_size,
                                          file_name=message.file_name,
                                          keyboard=kb)
        elif message.type == MessageType.CONTACT:
            contact = message.contact
            return v_messages.ContactMessage(contact=contact, keyboard=kb)
        elif message.type == MessageType.URL:
            return v_messages.URLMessage(media=message.url, keyboard=kb)
        elif message.type == MessageType.LOCATION:
            location = message.location
            return v_messages.LocationMessage(location=location, keyboard=kb)
        elif message.type == MessageType.RICHMEDIA:
            rich_media = message.rich_media
            return v_messages.RichMediaMessage(rich_media=rich_media,
                                               alt_text=(message.text or
                                                         message.alt_text),
                                               keyboard=kb)

    @staticmethod
    def _get_keyboard(buttons: List[Model]) -> dict:
        # TODO do refactoring
        vb_buttons = []

        for button in buttons:
            # if not isinstance(button, Button):
            #     continue

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

            try:
                if hasattr(button, 'image'):
                    domain = Site.objects.get_current().domain
                    vb_btn.update(BgMedia=f'https://{domain}{button.image}',
                                  BgMediaScaleType='fill')
            except IndexError:
                pass

            vb_buttons.append(vb_btn)

        keyboard = {
            'Type': 'keyboard',
            'BgColor': '#ffffff',
            'min_api_version': 6,
            'Buttons': vb_buttons,
        }

        return keyboard

    # endregion
