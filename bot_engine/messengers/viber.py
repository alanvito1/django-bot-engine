import logging
from typing import Any, Dict, List, Tuple, Union

from django.db.models import Model
from django.utils import timezone
from rest_framework.request import Request
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import (
    ContactMessage, FileMessage, KeyboardMessage, LocationMessage,
    PictureMessage, RichMediaMessage, StickerMessage, TextMessage,
    URLMessage, VideoMessage
)
from viberbot.api.viber_requests.viber_request import ViberRequest
from viberbot.api.viber_requests import (
    ViberMessageRequest, ViberConversationStartedRequest,
    ViberSubscribedRequest, ViberUnsubscribedRequest,
    ViberDeliveredRequest, ViberSeenRequest, ViberFailedRequest,
    create_request
)

from .base_messenger import BaseMessenger
from ..errors import MessengerException, NotSubscribed, RequestsLimitExceeded
from ..types import Message, MessageType


log = logging.getLogger(__name__)


class Viber(BaseMessenger):
    """
    IM connector for Viber REST API
    """
    #############
    # Interface #
    #############

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
        # {
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
        data = self.bot.get_account_info()
        account_info = {
            'id': data.get('id'),
            'username': data.get('name'),
            'info': data
        }
        return account_info

    def get_user_info(self, user_id: str, **kwargs) -> Dict[str, Any]:
        # {
        #    "status":0,
        #    "status_message":"ok",
        #    "message_token":4912661846655238145,
        #    "user":{
        #       "id":"01234567890A=",
        #       "name":"John McClane",
        #       "avatar":"http://avatar.example.com",
        #       "country":"UK",
        #       "language":"en",
        #       "primary_device_os":"android 7.1",
        #       "api_version":1,
        #       "viber_version":"6.5.0",
        #       "mcc":1,
        #       "mnc":1,
        #       "device_type":"iPhone9,4"
        #    }
        # }
        try:
            data = self.bot.get_user_details(user_id)
        except Exception as err:
            if 'failed with status: 12' in str(err):
                raise RequestsLimitExceeded(err)

        user_info = {
            'id': data.get('id'),
            'username': data.get('name'),
            'info': {
                'avatar': data.get('avatar'),
                'country': data.get('country'),
                'language': data.get('language'),
                'primary_device_os': data.get('primary_device_os'),
                'api_version': data.get('api_version'),
                'viber_version': data.get('viber_version'),
                'device_type': data.get('device_type'),
            }
        }
        return user_info

    def parse_message(self, request: Request) -> Message:
        # NOTE: There is no way to get the body
        #       after processing the request in DRF.
        # # Verify signature
        # sign = request.META.get('HTTP_X_VIBER_CONTENT_SIGNATURE')
        # if not self.bot.verify_signature(request.body, sign):
        #     raise IMApiException(f'Viber message not verified; '
        #                          f'Data={request.data}; Sign={sign};')

        vb_request = create_request(request.data)

        return self._get_message(vb_request)

    def send_message(self, receiver: str,
                     message: Union[Message, List[Message]]) -> List[str]:
        kb = self._get_keyboard(button_list) if button_list else None

        if message:
            vb_message = TextMessage(text=message, keyboard=kb)
        else:
            vb_message = KeyboardMessage(keyboard=kb)

        try:
            return self.bot.send_messages(receiver, [vb_message])[0]
        except Exception as err:
            if str(err) == 'failed with status: 6, message: notSubscribed':
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

    ################
    # Help methods #
    ################

    def send_file(self, receiver: str, file_url: str,
                  file_size: int, file_name: str, file_type: str = None,
                  button_list: list = None, **kwargs) -> str:
        kb = self._get_keyboard(button_list) if button_list else None

        if file_type == 'image':
            message = PictureMessage(media=file_url, keyboard=kb)
        elif file_type == 'video':
            message = VideoMessage(media=file_url, size=file_size, keyboard=kb)
        else:
            message = FileMessage(media=file_url, size=file_size,
                                  file_name=file_name, keyboard=kb)

        try:
            return self.bot.send_messages(receiver, [message])[0]
        except Exception as err:
            if str(err) == 'failed with status: 6, message: notSubscribed':
                raise NotSubscribed(err)
            raise MessengerException(err)

    @staticmethod
    def _get_message(request: ViberRequest) -> Message:
        log.debug(f'{request=}')

        if isinstance(request, ViberMessageRequest):
            log.debug(f'{request.message=}')

            if isinstance(request.message, TextMessage):
                msg_type = MessageType.TEXT
                if 'btn-' in request.message.text:
                    msg_type = MessageType.BUTTON
                return Message(
                    message_type=msg_type,
                    message_id=request.message_token,
                    user_id=request.sender.id,
                    text=request.message.text,
                    timestamp=request.timestamp)
            elif isinstance(request.message, PictureMessage):
                return Message(
                    message_type=MessageType.PICTURE,
                    message_id=request.message_token,
                    user_id=request.sender.id,
                    image_url=request.message.media,
                    timestamp=request.timestamp)
            elif isinstance(request.message, VideoMessage):
                return Message(
                    message_type=MessageType.PICTURE,
                    message_id=request.message_token,
                    user_id=request.sender.id,
                    video_url=request.message.media,
                    size=request.message.size,
                    timestamp=request.timestamp)
            elif isinstance(request.message, FileMessage):
                return Message(
                    message_type=MessageType.FILE,
                    message_id=request.message_token,
                    user_id=request.sender.id,
                    file_url=request.message.media,
                    size=request.message.size,
                    timestamp=request.timestamp)
            elif isinstance(request.message, RichMediaMessage):
                return Message(
                    message_type=MessageType.RICHMEDIA,
                    message_id=request.message_token,
                    user_id=request.sender.id,
                    text=request.message.rich_media,
                    alt_text=request.message.alt_text,
                    timestamp=request.timestamp)
            elif isinstance(request.message, URLMessage):
                return Message(
                    message_type=MessageType.URL,
                    message_id=request.message_token,
                    user_id=request.sender.id,
                    url=request.message.media,
                    timestamp=request.timestamp)
            elif isinstance(request.message, LocationMessage):
                return Message(
                    message_type=MessageType.LOCATION,
                    message_id=request.message_token,
                    user_id=request.sender.id,
                    location=request.message.location,
                    timestamp=request.timestamp)
            elif isinstance(request.message, ContactMessage):
                return Message(
                    message_type=MessageType.CONTACT,
                    message_id=request.message_token,
                    user_id=request.sender.id,
                    contact=request.message.contact,
                    timestamp=request.timestamp)
            elif isinstance(request.message, StickerMessage):
                return Message(
                    message_type=MessageType.STICKER,
                    message_id=request.message_token,
                    user_id=request.sender.id,
                    sticker_id=request.message.sticker_id,
                    timestamp=request.timestamp)
            elif isinstance(request.message, KeyboardMessage):
                return Message(
                    message_type=MessageType.KEYBOARD,
                    message_id=request.message_token,
                    user_id=request.sender.id,
                    text=request.message,
                    timestamp=request.timestamp)
            else:
                return Message(
                    message_type=MessageType.TEXT,
                    message_id=request.message_token,
                    user_id=request.sender.id,
                    text=request.message,
                    timestamp=request.timestamp)
        elif isinstance(request, ViberConversationStartedRequest):
            return Message(
                message_type=MessageType.START,
                message_id=request.message_token,
                user_id=request.user.id,
                user_name=request.user.name,
                timestamp=request.timestamp,
                context=request.context)
        elif isinstance(request, ViberSubscribedRequest):
            return Message(
                message_type=MessageType.SUBSCRIBED,
                user_id=request.user.id,
                user_name=request.user.name,
                timestamp=request.timestamp)
        elif isinstance(request, ViberUnsubscribedRequest):
            return Message(
                message_type=MessageType.UNSUBSCRIBED,
                user_id=request.user_id,
                timestamp=request.timestamp)
        elif isinstance(request, ViberDeliveredRequest):
            return Message(
                message_type=MessageType.DELIVERED,
                message_id=request.meesage_token,
                user_id=request.user_id,
                timestamp=request.timestamp)
        elif isinstance(request, ViberSeenRequest):
            return Message(
                message_type=MessageType.SEEN,
                message_id=request.meesage_token,
                user_id=request.user_id,
                timestamp=request.timestamp)
        elif isinstance(request, ViberFailedRequest):
            log.warning(f'Client failed receiving message; Error={request}')
            return Message(
                message_type=MessageType.FAILED,
                message_id=request.meesage_token,
                user_id=request.user_id,
                error=request.desc)
        elif request.event_type == 'webhook':
            return Message(
                message_type=MessageType.WEBHOOK,
                timestamp=request.timestamp)
        else:
            log.warning(f'VRequest Type={type(request)}; '
                        f'Object={request};')
            return Message(
                message_type=MessageType.UNDEFINED,
                timestamp=request.timestamp,
                event_type=request.event_type)
            # raise IMApiException('Failed parse message; '
            #                      'Request object={}'.format(viber_request))

    @staticmethod
    def _get_keyboard(buttons: list):
        if not buttons:
            return None

        kb = {
            'Type': 'keyboard',
            'BgColor': '#ffffff',
            'min_api_version': 6,
            'Buttons': []
        }

        for button in buttons:
            # if not isinstance(button, Button):
            #     continue

            _btn = {
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
                    _btn.update(
                        BgMedia=f'https://bot.it-o.ru/static/img/{button.image}',
                        BgMediaScaleType='fill')
            except IndexError:
                pass

            kb['Buttons'].append(_btn)

        return kb
