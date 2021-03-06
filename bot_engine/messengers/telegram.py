import json
import logging
from typing import Any, Dict, List, Union

from django.http.request import HttpRequest
# TODO: change tg api implementation to telethon
from telebot import apihelper, types

from .base_messenger import BaseMessenger
from ..errors import MessengerException
from ..types import (
    Message, Text, Contact, Location, RichMedia, Url, Button,
    File, Picture, Sticker, Audio, Video, Event, EType, MessageList
)


log = logging.getLogger(__name__)


class Telegram(BaseMessenger):
    """
    IM connector for Telegram Bot API
    """
    # region Interface

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
        try:
            photo_url = None
            data = apihelper.get_chat_member(
                self.token, kwargs.get('chat_id') or user_id, user_id
            )
            log.debug(f'User info data={data};')
        except Exception as err:
            raise MessengerException(err)

        try:
            photos = apihelper.get_user_profile_photos(self.token, user_id)
            data.update(photos=photos)

            log.debug(f'User photos={photos};')

            if photos['total_count'] > 0:
                photo_url = self.get_file_url(photos['photos'][0][0]['file_id'])
            data.update(avatar=photo_url, photos=photos)
        except Exception as err:
            raise MessengerException(err)

        return {
            'id': data['user']['id'],
            'username': data['user']['username'],
            'avatar': photo_url,
            'info': data
        }

    def parse_message(self, request: HttpRequest) -> Message:
        return self._from_tg_message(json.loads(request.body))

    def send_message(self, receiver: str,
                     messages: Union[Message, List[Message]]) -> List[str]:
        if isinstance(messages, MessageList):
            messages = messages.as_list()
        elif isinstance(messages, Message):
            messages = [messages]

        message_ids = []
        for message in messages:
            # try:
            message_id = self._send_message(receiver, message)
            message_ids.append(message_id)
            # except Exception as err:
            #     raise MessengerException(err)

        return message_ids

    # endregion

    # region Help methods

    def _from_tg_message(self, update: dict) -> Message:
        # update = {
        #     'update_id': 268489,
        #     'message': {
        #         'message_id': int,
        #         'from': User or None,
        #         'date': 1995468233,
        #         'chat': {'id': long, 'type': str, 'title': str,
        #             'username': str, 'first_name': str, 'last_name': str,
        #             'photo': ChatPhoto, 'description': str, 'invite_link': str,
        #             'pinned_message': Message, 'permissions': ChatPermissions,
        #             'slow_mode_delay': int, 'sticker_set_name': str, 'can_set_sticker_set': True},
        #         'forward_from': User or None,
        #         'forward_from_chat': Chat or None,
        #         'forward_from_message_id': Int or None,
        #         'forward_signature': Str on None,
        #         'forward_sender_name': Str on None,
        #         'forward_date': Int or None,
        #         'reply_to_message': Message or None,
        #         'edit_date': Int or None,
        #         'media_group_id': Str on None,
        #         'author_signature': Str on None,
        #         'text': Str on None,
        #         'entities': [{'type': str, 'offset': int, 'length': int, 'url': str or None, 'user': User or None, 'language': str or None}],
        #         'caption_entities': [MessageEntity],
        #         'audio': {'file_id': str, 'file_unique_id': str, 'duration': int, 'performer': str, 'title': str, 'thumb': PhotoSize, 'mime_type': str, 'file_size': int},
        #         'document': {'file_id': str, 'file_unique_id': str, 'thumb': PhotoSize, 'file_name': str, 'mime_type': str, 'file_size': int},
        #         'animation': {'file_id': str, 'file_unique_id': str, 'width': int, 'height': int, 'duration': int, 'thumb': PhotoSize, 'file_name': str, 'mime_type': str, 'file_size': int},
        #         'game': {'title': str, 'description': str, 'photo': [PhotoSize], 'text': str, 'text_entities': [MessageEntity], 'animation': Animation},
        #         'photo': [PhotoSize],
        #         'sticker': {'file_id': str, 'file_unique_id': str, 'width': int, 'height': int, 'is_animated': True, 'thumb': PhotoSize, 'emoji': str, 'set_name': str, 'mask_position': MaskPosition, 'file_size': int},
        #         'video': {'file_id': str, 'file_unique_id': str, 'width': int, 'height': int, 'duration': int, 'thumb': PhotoSize, 'mime_type': str, 'file_size': int},
        #         'voice': {'file_id': str, 'file_unique_id': str, 'duration': int, 'mime_type': str, 'file_size': int},
        #         'video_note': {'file_id': str, 'file_unique_id': str, 'length': int, 'duration': int, 'thumb': PhotoSize, 'file_size': int},
        #         'caption': str,
        #         'contact': {'phone_number': str, 'first_name': str, 'last_name': str, 'user_id': int, 'vcard': str},
        #         'location': {'longitude': float, 'latitude': float},
        #         'venue': {'location': Location, 'title': str, 'address': str, 'foursquare_id': str, 'foursquare_type': str},
        #         'poll': Poll,
        #         'new_chat_members': [User] or None,
        #         'left_chat_member': User or None,
        #         'new_chat_title': 'title' or None,
        #         'new_chat_photo': [PhotoSize] or None,
        #         'delete_chat_photo': True or None,
        #         'group_chat_created': True or None,
        #         'supergroup_chat_created': True or None,  # Skip
        #         'channel_chat_created': True or None,  # Skip
        #         'migrate_to_chat_id': 453 or None,
        #         'migrate_from_chat_id': 345 or None,
        #         'pinned_message': Message or None,
        #         'invoice': Invoice or None,
        #         'successful_payment': SuccessfulPayment or None,
        #         'connected_website': 'domain' or None,  # Tg Login
        #         'passport_data': PassportData or None,
        #         'reply_markup': InlineKeyboardMarkup or None,
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
        tg_message = (update.get('message') or
                      update.get('channel_post'))
        tg_edited_message = (update.get('edited_message') or
                             update.get('edited_channel_post'))
        user = tg_message.get('from')  # or chat?
        message_id = f'{user.get("id")}_{tg_message["message_id"]}'

        if tg_message.get('audio'):
            message = Audio(
                id=message_id,
                user_id=user.get('id'),
                timestamp=tg_message['date'],
                file_id=tg_message['audio']['file_id'],
                file_url=self.get_file_url(tg_message['audio']['file_id']),
                file_size=tg_message['audio'].get('file_size'),
                file_name=f'{tg_message["audio"].get("performer")} - '
                          f'{tg_message["audio"].get("title")}',
                file_duration=tg_message['audio'].get('duration'),
                file_mime_type=tg_message['audio'].get('mime_type'),
                text=tg_message.get('caption'),
                im_type='telegram'
            )
        elif tg_message.get('document'):
            message = File(
                id=message_id,
                user_id=user.get('id'),
                timestamp=tg_message['date'],
                file_id=tg_message['document']['file_id'],
                file_url=self.get_file_url(tg_message['document']['file_id']),
                file_size=tg_message['document'].get('file_size'),
                file_name=tg_message['document']['file_name'],
                file_mime_type=tg_message['document']['mime_type'],
                text=tg_message['document'].get('caption'),
                im_type='telegram')
        elif tg_message.get('animation'):
            message = File(
                id=message_id,
                user_id=user.get('id'),
                timestamp=tg_message['date'],
                file_id=tg_message['animation']['file_id'],
                file_url=self.get_file_url(tg_message['animation']['file_id']),
                file_size=tg_message['animation'].get('file_size'),
                file_name=tg_message['animation']['file_name'],
                file_mime_type=tg_message['animation'].get('mime_type'),
                text=tg_message.get('text'),
                context=tg_message.get('caption'),
                im_type='telegram')
        elif tg_message.get('game'):
            message = Message(
                id=message_id,
                user_id=user.get('id'),
                timestamp=tg_message['date'],
                game=tg_message['game'],
                text=tg_message.get('text'),
                context=tg_message.get('caption'),
                im_type='telegram')
        elif tg_message.get('photo'):
            if (isinstance(tg_message['photo'], list) and
                    len(tg_message['photo']) > 1):
                message = Picture(
                    id=message_id,
                    user_id=user.get('id'),
                    timestamp=tg_message['date'],
                    file_id=tg_message['photo'][-1]['file_id'],
                    file_url=self.get_file_url(tg_message['photo'][-1]['file_id']),
                    file_size=tg_message['photo'][-1].get('file_size'),
                    text=tg_message.get('text'),
                    context=tg_message.get('caption'),
                    im_type='telegram')
                # message = Message.multiple()
                # for photo in tg_message['photo'][0]:
                #     message += Message.picture(
                #         message_id=message_id,
                #         user_id=user.get('id'),
                #         timestamp=tg_message['date'],
                #         file_url=self.get_file_url(photo['file_id']),
                #         file_size=photo.get('file_size'),
                #         text=tg_message.get('text'),
                #         alt_text=tg_message.get('caption'),
                #         im_type='telegram')
            else:
                message = Picture(
                    id=message_id,
                    user_id=user.get('id'),
                    timestamp=tg_message['date'],
                    file_id=tg_message['photo'][-1]['file_id'],
                    file_url=self.get_file_url(tg_message['photo'][0][0]['file_id']),
                    file_size=tg_message['photo'][0][0].get('file_size'),
                    text=tg_message.get('text'),
                    context=tg_message.get('caption'),
                    im_type='telegram')
        elif tg_message.get('sticker'):
            message = Sticker(
                id=message_id,
                user_id=user.get('id'),
                timestamp=tg_message['date'],
                file_id=tg_message['sticker']['file_id'],
                file_url=self.get_file_url(tg_message['sticker']['file_id']),
                file_size=tg_message['sticker'].get('file_size'),
                im_type='telegram')
        elif tg_message.get('video'):
            message = Video(
                id=message_id,
                user_id=user.get('id'),
                timestamp=tg_message['date'],
                file_id=tg_message['video']['file_id'],
                file_url='',
                # file_url=self.get_file_url(tg_message['video']['file_id']),
                file_size=tg_message['video'].get('file_size'),
                file_duration=tg_message['video'].get('duration'),
                file_mime_type=tg_message['video'].get('mime_type'),
                text=tg_message['video'].get('caption'),
                im_type='telegram'
            )
        elif tg_message.get('voice'):
            message = Audio(
                id=message_id,
                user_id=user.get('id'),
                timestamp=tg_message['date'],
                file_id=tg_message['voice']['file_id'],
                file_url=self.get_file_url(tg_message['voice']['file_id']),
                file_size=tg_message['voice'].get('file_size'),
                file_duration=tg_message['voice'].get('duration'),
                file_mime_type=tg_message['voice'].get('mime_type'),
                is_voice=True,
                text=tg_message.get('caption'),
                im_type='telegram'
            )
        elif tg_message.get('video_note'):
            message = Video(
                id=message_id,
                user_id=user.get('id'),
                timestamp=tg_message['date'],
                file_id=tg_message['video_note']['file_id'],
                file_url=self.get_file_url(tg_message['video_note']['file_id']),
                file_size=tg_message['video_note'].get('file_size'),
                file_duration=tg_message['video_note'].get('duration'),
                # file_length=tg_message['video_note'].get('length'),
                is_video_note=True,
                text=tg_message.get('text'),
                context=tg_message.get('caption'),
                im_type='telegram'
            )
        elif tg_message.get('contact'):
            message = Contact(
                id=message_id,
                user_id=user.get('id'),
                timestamp=tg_message['date'],
                contact=tg_message['contact'],
                text=tg_message.get('text'),
                context=tg_message.get('caption'),
                im_type='telegram'
            )
        elif tg_message.get('location'):
            message = Location(
                id=message_id,
                user_id=user.get('id'),
                timestamp=tg_message['date'],
                location=tg_message['location'],
                text=tg_message.get('text'),
                context=tg_message.get('caption'),
                im_type='telegram'
            )
        elif tg_message.get('venue'):
            message = Location(
                id=message_id,
                user_id=user.get('id'),
                timestamp=tg_message['date'],
                location=tg_message['venue']['location'],
                text=tg_message['venue']['title'] or tg_message.get('text'),
                context=tg_message['venue']['address'] or tg_message.get('caption'),
                im_type='telegram'
            )
        else:
            message = Text(
                id=message_id,
                user_id=user.get('id'),
                timestamp=tg_message['date'],
                text=tg_message.get('text'),
                context=tg_message.get('caption'),
                im_type='telegram'
            )

        if message.text == '/start':
            message = Event(
                id=message_id,
                user_id=user.get('id'),
                timestamp=tg_message['date'],
                event_type=EType.START,
            )

        return message

    def _send_message(self, receiver: str, message: Message) -> str:
        if message.buttons:
            kb = types.ReplyKeyboardMarkup()
            kb.add(*[x.text for x in message.buttons])
        else:
            kb = None

        reply_to_id = (message.reply_to_id.split('_')[1]
                       if message.reply_to_id else None)

        # TODO implement chat work. now only tet-a-tet
        receiver = receiver.split('_')[0]

        if isinstance(message, Text):
            msg_id = apihelper.send_message(
                self.token, receiver, message.text,
                reply_to_message_id=reply_to_id,
                reply_markup=kb
            )
        elif isinstance(message, Sticker):
            method_name = 'sendSticker'
            data = {'chat_id': receiver, 'sticker': message.file_id}
            if reply_to_id:
                data.update(reply_to_message_id=reply_to_id)
            msg_id = apihelper._make_request(
                self.token, method_name,
                params=data, method='post'
            )
        elif isinstance(message, Picture):
            picture = message.file_id or message.file_url
            msg_id = apihelper.send_photo(
                self.token, receiver, picture,
                caption=message.text,
                reply_to_message_id=reply_to_id,
                reply_markup=kb
            )
        elif isinstance(message, Audio):
            audio = message.file_id or message.file_url
            if message.is_voice:
                msg_id = apihelper.send_voice(
                    self.token, receiver, audio,
                    duration=message.file_duration,
                    caption=message.text,
                    reply_to_message_id=reply_to_id,
                    reply_markup=kb
                )
            else:
                msg_id = apihelper.send_audio(
                    self.token, receiver, audio,
                    title=message.file_name,
                    duration=message.file_duration,
                    caption=message.text,
                    reply_to_message_id=reply_to_id,
                    reply_markup=kb
                )
        elif isinstance(message, Video):
            video = message.file_id or message.file_url
            if message.is_video_note:
                msg_id = apihelper.send_video_note(
                    self.token, receiver, video,
                    duration=message.file_duration,
                    # length=message.file_length,
                    reply_to_message_id=reply_to_id,
                    reply_markup=kb
                )
            else:
                msg_id = apihelper.send_video(
                    self.token, receiver, video,
                    duration=message.file_duration,
                    caption=message.text,
                    reply_to_message_id=reply_to_id,
                    reply_markup=kb
                )
        elif isinstance(message, File):
            data = message.file_id or message.file_url
            data_type = 'document'
            msg_id = apihelper.send_data(
                self.token, receiver, data, data_type,
                caption=message.text,
                reply_to_message_id=reply_to_id,
                reply_markup=kb
            )
        elif isinstance(message, Contact):
            contact = message.contact
            msg_id = apihelper.send_contact(
                self.token, receiver,
                contact.get('phone'),
                contact.get('first_name'),
                reply_to_message_id=reply_to_id,
                reply_markup=kb
            )
        elif isinstance(message, Url):
            msg_id = apihelper.send_message(
                self.token, receiver, message.text,
                reply_to_message_id=reply_to_id,
                reply_markup=kb
            )
        elif isinstance(message, Location):
            location = message.location
            msg_id = apihelper.send_location(
                self.token, receiver,
                location.get('latitude'),
                location.get('longitude'),
                reply_to_message_id=reply_to_id,
                reply_markup=kb
            )
        elif isinstance(message, RichMedia):
            msg_id = apihelper.send_message(
                self.token, receiver, message.text,
                parse_mode=message.rich_media,
                reply_to_message_id=reply_to_id,
                reply_markup=kb
            )
        else:
            msg_id = apihelper.send_message(
                self.token, receiver, message.context,
                reply_to_message_id=reply_to_id,
                reply_markup=kb
            )

        return f'{receiver}_{msg_id}'

    def get_file_url(self, file_id: str) -> str:
        # TODO make download and save on this server
        try:
            file = apihelper.get_file(self.token, file_id)
            url = f'https://api.telegram.org/file/bot{self.token}/{file["file_path"]}'
        except Exception as err:
            log.exception(err)
            return ''
        return url

    # def save_file(self, file_id: str) -> str:
    #     file_name = f'{file_id}.png'
    #     domain = Site.objects.get_current().domain
    #     file_url = f'https://{domain}{settings.MEDIA_URL}tg/{file_name}'
    #     file = self.bot.get_file(file_id)
    #     with open(f'{settings.MEDIA_ROOT}tg/{file_name}', 'wb') as fd:
    #         fd.write(file)
    #     return file_url

    # endregion

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
