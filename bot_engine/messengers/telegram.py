import json
import logging
from typing import Any, Dict, List, Tuple, Union

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Model
from rest_framework.request import Request
# TODO: Independently implement or find a project with a more permissive license
from telebot import TeleBot, apihelper, types

from .base_messenger import BaseMessenger
from ..errors import MessengerException
from ..types import MessageType, Message


log = logging.getLogger(__name__)


class Telegram(BaseMessenger):
    """
    IM connector for Telegram Bot API
    """
    #############
    # Interface #
    #############

    def __init__(self, token: str, **kwargs):
        super().__init__(token, **kwargs)

        self.bot = TeleBot(token=token)
        if self.proxy_addr:
            apihelper.proxy = self.proxy_addr

    def enable_webhook(self, url: str, **kwargs):
        return self.bot.set_webhook(url=url)

    def disable_webhook(self):
        return self.bot.remove_webhook()

    def get_account_info(self) -> Dict[str, Any]:
        data = self.bot.get_me()
        # {
        #     'id': 0123,
        #     'first_name': 'name',
        #     'last_name': 'name',
        #     'username': 'name'
        # }
        account_info = {
            'id': data.get('id'),
            'username': data.get('username'),
            'info': data
        }
        return account_info

    def get_user_info(self, user_id: str, **kwargs) -> Dict[str, Any]:
        photo_url = None
        data = self.bot.get_chat_member(kwargs.get('chat_id'), user_id)
        # {
        #     'id': 0123,
        #     'first_name': 'name',
        #     'last_name': 'name',
        #     'username': 'name'
        # }
        log.debug(f'User info data={data}')
        photos = self.bot.get_user_profile_photos(user_id)
        # {
        #     'total_count': 123,
        #     'photos': [{
        #         'id': 'uid',
        #         'width': 10,
        #         'height': 10,
        #         'file_size': 123,
        #     }]
        # }
        log.debug(f'User photo data={photos}')
        if photos.total_count > 0:
            log.debug(f'One photo={photos.photos[0][0]}')
            photo_url = self.save_file(photos.photos[0][0].file_id)

        user_info = {
            'id': data.user.id,
            'username': data.user.username,
            'info': {
                'avatar': photo_url,
                'first_name': data.user.first_name,
                'last_name': data.user.last_name,
            }
        }
        return user_info

    def parse_message(self, request: Request) -> Message:
        try:
            update = request.data
            message = Message(
                message_type=MessageType.TEXT,
                message_id=update.get('message', {}).get('message_id', ''),
                user_id=update.get('message', {}).get('from', {}).get('id', ''),
                text=update.get('message').get('text', ''),
                timestamp=update.get('message').get('date', ''), )
            return message
        except Exception as err:
            raise MessengerException(err)

    def preprocess_message(self, message: Message, account: Model) -> Message:
        if message.type == MessageType.TEXT and account.menu:
            for button in account.menu.buttons.all():
                if message.text == button.text:
                    message.type = MessageType.BUTTON
        return message

    def send_message(self, receiver: str,
                     message: Union[Message, List[Message]]) -> List[str]:
        kb = types.ReplyKeyboardMarkup(row_width=3)
        for btn in button_list or []:
            kb.add(types.KeyboardButton(btn.text))
        return self.bot.send_message(chat_id=receiver, text=message,
                                     reply_markup=kb)

    def welcome_message(self, text: str) -> Union[str, Dict[str, Any], None]:
        return None

    ################
    # Help methods #
    ################

    def save_file(self, file_id: str) -> str:
        file_name = f'{file_id}.png'
        domain = Site.objects.get_current().domain
        file_url = f'https://{domain}{settings.MEDIA_URL}tg/{file_name}'
        file = self.bot.get_file(file_id)
        with open(f'{settings.MEDIA_ROOT}tg/{file_name}', 'wb') as fd:
            fd.write(file)
        return file_url

    # getMe
    # sendMessage
    # forwardMessage
    # sendPhoto
    # sendAudio
    # sendDocument
    # sendSticker
    # sendVideo
    # sendVoice
    # sendLocation
    # sendVenue
    # sendContact
    # sendChatAction
    # getUserProfilePhotos
    # getFile
    # kickChatMember
    # unbanChatMember
    # answerCallbackQuery
    # editMessageText
    # editMessageCaption
    # editMessageReplyMarkup
    # #################### Inline methods
    # object InlineQuery
    # answerInlineQuery
    # object InlineQueryResult
    # objects InlineQueryResultArticle, etc.
    # object InputMessageContent
    # ChosenInlineResult
