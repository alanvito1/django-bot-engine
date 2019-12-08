import logging

from django.http import HttpRequest

from .types import Button, Message, KeyboardMessage, TextMessage
from .imconnectors.imconnector import IMConnector
from .models import MenuItem


__all__ = ('BaseBot', 'EchoBot')

log = logging.getLogger(__name__)


class BaseBot:
    """
    Chatbots base class.
    """
    def __init__(self, api: IMConnector):
        self.api = api

    def dispatch(self, request: HttpRequest):
        """
        Parse the message from the request and send it to processing
        :param request:
        :return:
        """
        message = self.api.parse_message(request)

        if (isinstance(message, (TextMessage, KeyboardMessage))
                and 'BTN_MI_' in message.text):
            return self.process_menu_item(message)

        method_name = 'process_{}'.format(message.type)
        if hasattr(self, method_name):
            getattr(self, method_name)(message)
        else:
            self.process_message(message)

    def process_message(self, message: Message):
        """
        Processes any message for which
        no handler_class method was found.
        """
        raise NotImplementedError('This method must be implemented '
                                  'in child classes.')

    def process_menu_item(self, message: TextMessage):
        """
        Process an incoming message as a menu item type
        :param message:
        :return:
        """
        item = None
        command = message.text.replace('BTN_MI_', '')
        try:
            item = MenuItem.objects.get(cmd=command)
        except MenuItem.DoesNotExist as err:
            log.exception('Menu Item not found; Error={};'.format(err))
            self.process_exception(message, err)

        try:
            if item.handler_method:
                menu_item_handler = getattr(self, str(item.handler_method))
                menu_item_handler(message)
            else:
                menu = item.next_menu
                buttons = menu.as_button_list()
                answer = menu.text

                self.api.send_message(receiver=message.user_id,
                                      message=answer,
                                      button_list=buttons)
        except AttributeError as err:
            log.exception('process_menu_item error={};'.format(err))
            self.process_exception(message, err)

    def process_exception(self, message: Message, error: Exception):
        """
        Handles an exception caused by an incoming message.
        :param message:
        :param error:
        :return:
        """
        self.api.send_message(message.user_id, str(error))


class EchoBot(BaseBot):
    """
    Simple echo chat bot.
    """
    def process_text(self, message: TextMessage):
        if message.user_id:
            self.api.send_message(receiver=message.user_id,
                                  message=message.text)

    def process_message(self, message: Message):
        if message.is_common:
            self.api.send_message(receiver=message.user_id,
                                  message=str(message))
