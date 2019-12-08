import logging
from typing import Any, Dict, List

from django.http import HttpRequest
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import (
    TextMessage, FileMessage
)
from viberbot.api.viber_requests import (
    ViberMessageRequest, ViberConversationStartedRequest,
    ViberSubscribedRequest, ViberUnsubscribedRequest,
    ViberDeliveredRequest, ViberSeenRequest, ViberFailedRequest
)

from .imconnector import IMConnector
from ..errors import IMApiException
from ..types import Button, Message


log = logging.getLogger('bot_api')


class Viber(IMConnector):
    """
    IM connector for Viber REST API
    """

    def __init__(self, token: str, **kwargs):
        super().__init__(token, **kwargs)

        self.bot = Api(
            BotConfiguration(
                auth_token=token,
                name=kwargs.get('name'),
                avatar=kwargs.get('avatar_url')))

    def enable_webhook(self, uri: str, **kwargs):
        return self.bot.set_webhook(url=uri)

    def disable_webhook(self):
        return self.bot.unset_webhook()

    def get_account_info(self) -> Dict[str, Any]:
        return self.bot.get_account_info()

    def get_user_info(self, user_id: str, **kwargs) -> Dict[str, Any]:
        return self.bot.get_user_details(user_id)

    def parse_message(self, request: HttpRequest) -> Message:
        data = request.body

        # Verify signature
        sign = str(request.META.get('HTTP_X_VIBER_CONTENT_SIGNATURE'))
        if not self.bot.verify_signature(data, sign):
            raise IMApiException('Viber message not verified; '
                                 'Data={}; Sign={};'.format(data, sign))

        # Parse message data in to viber types
        vb_request = self.bot.parse_request(data.decode('utf-8'))

        try:
            return self._get_message(vb_request)
        except Exception as err:
            # TODO: remove this after development
            log.exception('Parse message error; Message={}; Error={};'.format(
                vb_request, err))
            return Message(Message.UNDEFINED)

    @staticmethod
    def _get_message(viber_request) -> Message:
        if isinstance(viber_request, ViberMessageRequest):
            if isinstance(viber_request.message, TextMessage):
                return Message.from_type(
                    message_type=Message.TEXT,
                    message_id=viber_request.message_token,
                    user_id=viber_request.sender.id,
                    text=viber_request.message.text,
                    date=viber_request.timestamp)
            else:
                return Message.from_type(
                    message_type=Message.TEXT,
                    message_id=viber_request.message_token,
                    user_id=viber_request.sender.id,
                    text=viber_request.message,
                    date=viber_request.timestamp)
        elif isinstance(viber_request, ViberConversationStartedRequest):
            return Message.from_type(
                message_type=Message.START,
                message_id=viber_request.message_token,
                user_id=viber_request.user.id,
                user_name=viber_request.user.name,
                data=viber_request.timestamp,
                context=viber_request.context)
        elif isinstance(viber_request, ViberSubscribedRequest):
            return Message.from_type(
                message_type=Message.SUBSCRIBED,
                user_id=viber_request.user.id,
                user_name=viber_request.user.name,
                data=viber_request.timestamp)
        elif isinstance(viber_request, ViberUnsubscribedRequest):
            return Message.from_type(
                message_type=Message.UNSUBSCRIBED,
                user_id=viber_request.user_id,
                data=viber_request.timestamp)
        elif isinstance(viber_request, ViberDeliveredRequest):
            return Message.from_type(
                message_type=Message.DELIVERED,
                message_id=viber_request.meesage_token,
                user_id=viber_request.user_id,
                data=viber_request.timestamp)
        elif isinstance(viber_request, ViberSeenRequest):
            return Message.from_type(
                message_type=Message.SEEN,
                message_id=viber_request.meesage_token,
                user_id=viber_request.user_id,
                timestamp=viber_request.timestamp)
        elif isinstance(viber_request, ViberFailedRequest):
            log.warning('Client failed receiving message; '
                        'Error={}'.format(viber_request))
            return Message.from_type(
                message_type=Message.FAILED,
                message_id=viber_request.meesage_token,
                user_id=viber_request.user_id,
                description=viber_request.desc)
        elif viber_request.event_type == 'webhook':
            return Message.from_type(
                message_type=Message.WEBHOOK,
                timestamp=viber_request.timestamp)
        else:
            log.warning('VRequest Type={}; Object={};'.format(
                type(viber_request), viber_request))
            return Message.from_type(
                message_type=Message.UNDEFINED,
                timestamp=viber_request.timestamp,
                event_type=viber_request.event_type)
            # raise IMApiException('Failed parse message; '
            #                      'Request object={}'.format(viber_request))

    def send_message(self, receiver: str, message: str,
                     button_list: List[Button] = None, **kwargs) -> str:
        kb = self._get_keyboard(button_list) if button_list else None
        return self.bot.send_messages(
            receiver,
            [TextMessage(text=message, keyboard=kb)])[0]

    def send_file(self, receiver: str, file_url: str,
                  file_size: int, file_name: str,
                  button_list: List[Button] = None, **kwargs) -> str:
        kb = self._get_keyboard(button_list) if button_list else None
        message = FileMessage(
            media=file_url,
            size=file_size,
            file_name=file_name,
            keyboard=kb)
        return self.bot.send_messages(receiver, [message])[0]

    @staticmethod
    def _get_keyboard(buttons: List[Button]):
        if not buttons:
            return None

        kb = {
            'Type': 'keyboard',
            'BgColor': '#ffffff',
            'min_api_version': 6,
        }
        _btns = []

        for btn in buttons:
            if not isinstance(btn, Button):
                continue

            _btn = {
                'Columns': btn.size[0],
                'Rows': btn.size[1],
                'BgColor': '#aaaaaa',
                'ActionType': 'reply',
                'ActionBody': btn.cmd,
                'Text': '<font color="{clr}"><b>{text}'
                        '</b></font>'.format(text=btn.text, clr='#131313'),
                'TextVAlign': 'middle', 'TextHAlign': 'center',
                'TextOpacity': 60, 'TextSize': 'large',
                'TextPaddings': [12, 8, 8, 20],  # [up, left, right, bottom]
            }

            try:
                if btn.image:
                    _btn.update(
                        BgMedia='https://service.it-o.ru/static/img/' + btn.image,
                        BgMediaScaleType='fill')
            except IndexError:
                pass

            _btns.append(_btn)

        kb.update(Buttons=_btns)

        return kb
