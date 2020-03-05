import logging
from typing import Any, Dict, List, Union

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Model
from rest_framework.request import Request
# TODO: Independently implement or find a project with a more permissive license
from telebot import apihelper, types

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

        if self.proxy_addr:
            apihelper.proxy = self.proxy_addr

    def enable_webhook(self, url: str, **kwargs):
        return apihelper.set_webhook(self.token, url)

    def disable_webhook(self):
        return apihelper.set_webhook(self.token)

    def get_account_info(self) -> Dict[str, Any]:
        # data = {
        #     'id': 0123,
        #     'first_name': 'name',
        #     'last_name': 'name',
        #     'username': 'name',
        #     'is_bot': True,
        #     'language_code': None
        # }
        try:
            data = apihelper.get_me(self.token)
        except Exception as err:
            raise MessengerException(err)

        return {
            'id': data.get('id'),
            'username': data.get('username'),
            'uri': f'http://t.me/{data.get("username")}',
            'info': data
        }

    def get_user_info(self, user_id: str, **kwargs) -> Dict[str, Any]:
        # data = {
        #     'user': {
        #         'id': id,
        #         'is_bot': is_bot,
        #         'first_name': first_name,
        #         'username': username,
        #         'last_name': last_name,
        #         'language_code': language_code,
        #     },
        #     'status': 'status',
        #     'until_date': None,
        #     'can_be_edited': None,
        #     'can_change_info': None,
        #     'can_post_messages': None,
        #     'can_edit_messages': None,
        #     'can_delete_messages': None,
        #     'can_invite_users': None,
        #     'can_restrict_members': None,
        #     'can_pin_messages': None
        #     'can_promote_members': None,
        #     'can_send_messages': None,
        #     'can_send_media_messages': None,
        #     'can_send_other_messages': None,
        #     'can_add_web_page_previews': None,
        # }
        try:
            photo_url = None
            data = apihelper.get_chat_member(self.token,
                                             kwargs.get('chat_id') or user_id,
                                             user_id)
            log.debug(f'User info data={data};')
        except Exception as err:
            raise MessengerException(err)

        # photos = {
        #     'total_count': 123,
        #     'photos': [{
        #         'id': 'uid',
        #         'width': 10,
        #         'height': 10,
        #         'file_size': 123,
        #     }, ]
        # }
        try:
            photos = apihelper.get_user_profile_photos(self.token, user_id)
            data.update(photos=photos)

            log.debug(f'User photos={photos};')

            if photos['total_count'] > 0:
                # 'https://api.telegram.org/file/bot{0}/{1}'.format(API_TOKEN, file_info.file_path)
                photo_url = ''  # self.save_file(photos['photos'][0][0].file_id)
                # TODO make simple photo url
            data.update(avatar=photo_url)
        except Exception as err:
            raise MessengerException(err)

        return {
            'id': data['user']['id'],
            'username': data['user']['username'],
            'avatar': photo_url,
            'info': data
        }

    def parse_message(self, request: Request) -> Message:
        r_data = request.data

        return self._from_tg_message(r_data)

    def send_message(self, receiver: str,
                     messages: Union[Message, List[Message]]) -> List[str]:
        message_ids = []

        if not isinstance(messages, list):
            messages = [messages]

        for message in messages:
            try:
                message_id = self._send_message(receiver, message)
                message_ids.append(message_id)
            except Exception as err:
                raise err

        return message_ids

    ################
    # Help methods #
    ################

    def _from_tg_message(self, update: dict) -> Message:
        # update = {
        #     'update_id': 268489,
        #     'message': {
        #         'message_id': 6,
        #         'from': User or None,
        #         'date': 1995468233,
        #         'edit_date': 1995468233,
        #         'chat': Chat,
        #         'from': User,
        #         '': ,
        #     },
        #     'edited_message': Message,
        #     'channel_post': Message,
        #     'edited_channel_post': Message,
        #     'inline_query': {'from': User, 'location': Location or None, 'query': 'query', 'offset': 'offset', },
        #     'chosen_inline_result': {'result_id': 2, 'from': User, 'query': 'query', 'location': Location or None, 'inline_message_id': 465, },
        #     'callback_query': {'id': 984, 'from': User, 'message': Message or None, 'inline_message_id': 465, 'chat_instance': 'chat', 'data': 'data', 'game_short_name': 'game', },
        #     'shipping_query': {'id': 64, 'from': User, 'invoice_payload': 'invoice_payload', 'shipping_address': ShippingAddress, },
        #     'pre_checkout_query': {'id': 65, 'from': User, 'currency': 'ISO 4217', 'total_amount': 465, 'invoice_payload': 'invoice_payload', 'shipping_option_id': '242', 'order_info': OrderInfo or None, },
        #     'poll': {'id': 'id', 'question': 'question', 'options': [PollOption], 'total_voter_count': 8, 'is_closed': True, 'is_anonymous': True, 'type': 'type', 'allows_multiple_answers': True, 'correct_option_id': 5, },
        #     'poll_answer': {'poll_id': 'poll_id', 'user': User, 'option_ids': [int]}
        # }
        tg_message = update.get('message')

        message = Message.text(
            message_id=tg_message.get('message_id'),
            user_id=tg_message.get('from', {}).get('id'),
            text=tg_message.get('text', ''),
            timestamp=tg_message.get('date')
        )

        return message

    # def _to_tg_message(self, message: Message) -> dict:
    #
    #     kb = types.ReplyKeyboardMarkup(row_width=3)
    #     for btn in button_list or []:
    #         kb.add(types.KeyboardButton(btn.text))
    #
    #     return {}

    def _send_message(self, receiver: str, message: Message) -> str:
        # tg_message = self._to_tg_message(message)

        if message.type == MessageType.TEXT:
            msg_id = apihelper.send_message(self.token, receiver, message.text)
        elif message.type == MessageType.STICKER:
            msg_id = apihelper.send_message(self.token, receiver, message.text)
        elif message.type == MessageType.PICTURE:
            msg_id = apihelper.send_photo(self.token, receiver, message.text)
        elif message.type == MessageType.AUDIO:
            msg_id = apihelper.send_audio(self.token, receiver, message.text)
        elif message.type == MessageType.VIDEO:
            msg_id = apihelper.send_video(self.token, receiver, message.text)
        elif message.type == MessageType.FILE:
            msg_id = apihelper.send_data(self.token, receiver, message.text)
        elif message.type == MessageType.CONTACT:
            msg_id = apihelper.send_contact(self.token, receiver, message.text)
        elif message.type == MessageType.URL:
            msg_id = apihelper.send_message(self.token, receiver, message.text)
        elif message.type == MessageType.LOCATION:
            msg_id = apihelper.send_location(self.token, receiver, message.text)
        elif message.type == MessageType.RICHMEDIA:
            msg_id = apihelper.send_message(self.token, receiver, message.text)
        elif message.type == MessageType.KEYBOARD:
            msg_id = apihelper.send_message(self.token, receiver, message.text)
        else:
            msg_id = apihelper.send_message(self.token, receiver, message.text)

        return f'{receiver}_{msg_id}'

    # def save_file(self, file_id: str) -> str:
    #     file_name = f'{file_id}.png'
    #     domain = Site.objects.get_current().domain
    #     file_url = f'https://{domain}{settings.MEDIA_URL}tg/{file_name}'
    #     file = self.bot.get_file(file_id)
    #     with open(f'{settings.MEDIA_ROOT}tg/{file_name}', 'wb') as fd:
    #         fd.write(file)
    #     return file_url

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
