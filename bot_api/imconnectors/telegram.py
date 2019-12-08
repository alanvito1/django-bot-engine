import json
import logging
from typing import Any, Dict, List

from django.http import HttpRequest
from telebot import TeleBot, apihelper, types

from .imconnector import IMConnector
from ..errors import IMApiException
from ..types import Button, Message


log = logging.getLogger('bot_api')


class Telegram(IMConnector):
    """
    IM connector for Telegram Bot API
    """
    def __init__(self, token: str, proxy: str = None, **kwargs):
        super().__init__(token, **kwargs)

        self.bot = TeleBot(token=token)
        if proxy:
            apihelper.proxy = self._proxy(proxy)

    def enable_webhook(self, uri: str, **kwargs):
        return self.bot.set_webhook(url=uri)

    def disable_webhook(self):
        return self.bot.remove_webhook()

    def get_account_info(self) -> Dict[str, Any]:
        return self.bot.get_me()

    def get_user_info(self, user_id: str, **kwargs) -> Dict[str, Any]:
        return self.bot.get_chat_member(kwargs.get('chat_id'), user_id)

    def parse_message(self, request: HttpRequest) -> Message:
        log.debug('Data={};'.format(request.body.decode('utf-8')))
        try:
            json_string = request.body.decode('utf-8')
            update = json.loads(json_string)
            message = Message.from_type(
                message_type=Message.TEXT,
                message_id=update.get('message', {}).get('message_id', ''),
                user_id=update.get('message', {}).get('from', {}).get('id', ''),
                text=update.get('message').get('text', ''),
                timestamp=update.get('message').get('date', ''), )
            return message
        except Exception as err:
            log.exception('Error={};'.format(err))

    def send_message(self, receiver: str, message: str,
                     button_list: List[Button] = None, **kwargs) -> str:
        return self.bot.send_message(chat_id=receiver, text=message)
