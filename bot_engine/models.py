from __future__ import annotations
import logging
from hashlib import md5
from typing import Any, Callable, List, Optional, Type
from uuid import uuid4

from django.conf import settings
# TODO make a custom JSONField inherited from TextField for others db's
from django.contrib.postgres.fields import JSONField
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.module_loading import import_string
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from rest_framework.request import Request
from sortedm2m.fields import SortedManyToManyField

from .errors import MessengerException, NotSubscribed, RequestsLimitExceeded
from .messengers import BaseMessenger, MessengerType
from .types import Message, MessageType


__all__ = ('Account', 'Button', 'Menu', 'Messenger')

log = logging.getLogger(__name__)

DOMAIN = Site.objects.get_current().domain
ECHO_HANDLER = 'bot_engine.bot_handlers.simple_echo'
BUTTON_HANDLER = 'bot_engine.bot_handlers.button_echo'
BASE_HANDLER = ECHO_HANDLER


class Messenger(models.Model):
    title = models.CharField(
        _('title'), max_length=256,
        help_text=_('This name will be used as the sender name.'))
    api_type = models.CharField(
        _('API type'), max_length=256,
        choices=MessengerType.choices(),
        default=MessengerType.NONE.value)
    token = models.CharField(
        _('bot token'), max_length=256,
        default='', blank=True,
        help_text=_('Token or secret key.'))
    proxy = models.CharField(
        _('proxy'), max_length=256,
        default='', blank=True,
        help_text=_('Enter proxy uri with format '
                    '"schema://user:password@proxy_address:port"'))
    logo = models.CharField(
        _('logo'), max_length=256,
        default='', blank=True,
        help_text=_('Relative URL. Required for some messenger APIs: Viber.'))
    welcome_text = models.TextField(
        _('welcome text'),
        default='', blank=True,
        help_text=_('Welcome message. Will be sent in response to the opening'
                    ' of the dialog (not a subscribe event). May be used with'
                    ' some messaging programs: Viber.'))

    handler = models.CharField(
        _('main handler'), max_length=256,
        default=BASE_HANDLER, blank=True,
        help_text=_('It processes all messages that do not fall into '
                    'the menu and button handlers. To implement a handler, '
                    f'implement a {BASE_HANDLER} interface.'))
    menu = models.ForeignKey(
        'Menu', models.SET_NULL,
        verbose_name=_('main menu'), related_name='messengers',
        null=True, blank=True,
        help_text=_('The root menu. For example, "Home".'))

    hash = models.CharField(
        _('token hash'), max_length=256,
        default='', editable=False)
    is_active = models.BooleanField(
        _('active'),
        default=False, editable=False,
        help_text=_('This flag changes when the webhook on the messenger API '
                    'server is activated/deactivated.'))
    updated = models.DateTimeField(
        _('updated'), auto_now=True)
    created = models.DateTimeField(
        _('created'), auto_now_add=True)

    class Meta:
        verbose_name = _('messenger')
        verbose_name_plural = _('messengers')
        unique_together = ('token', 'api_type')

    def __str__(self):
        return f'{self.title} ({self.api_type})'

    def __repr__(self):
        _hash = self.token_hash
        return f'<bot_engine.Messenger object ({self.api_type}:{_hash})>'

    def get_url_activating_webhook(self):
        return reverse('bot_engine:activate', kwargs={'id': self.id})

    def get_url_deactivating_webhook(self):
        return reverse('bot_engine:deactivate', kwargs={'id': self.id})

    @property
    def token_hash(self) -> str:
        if not self.hash:
            self.hash = md5(self.token.encode()).hexdigest()
            self.save()
        return self.hash

    def dispatch(self, request: Request) -> Optional[Any]:
        """
        Entry point for current messenger account
        :param request: Rest framework request object
        :return: Answer data (optional)
        """
        message = self.api.parse_message(request)

        log.debug(f'Dispatch; Incoming message={message};')

        if message.user_id:
            default = {
                'username': message.user_name or message.user_id,
                'messenger': self,
                'menu': self.menu,
                'is_active': True,
            }
            account, created = Account.objects.get_or_create(id=message.user_id,
                                                             defaults=default)
            if created or not account.info:
                account.update_info()
        else:
            account = None

        # log.debug(f'Dispatch; Message={message}; Account={account};')

        if message.is_service:
            # TODO make service handler
            if (message.type == MessageType.START and account
                    and self.welcome_text):
                account.send_message(Message.text(text=self.welcome_text))
                return self.api.welcome_message(self.welcome_text)
            elif message.type == MessageType.UNSUBSCRIBED and account:
                account.update(is_active=False)
            # self.process_service_message(message, account)
            return None

        message = self.preprocess_message(message, account)

        if account.menu:
            account.menu.process_message(message, account)
        else:
            self.process_message(message, account)

    def preprocess_message(self, message: Message, account: Account) -> Message:
        """
        Pre-process message data
        Some messengers can understand the message only in context,
        e.g. Telegram(from text to button)
        :param message: bot_engine.Message object
        :param account: bot_engine.Account object
        :return: Message object
        """
        if self.api_type in [MessengerType.VIBER]:
            return message

        if (self.api_type in [MessengerType.TELEGRAM.value] and
                message.type == MessageType.TEXT and account.menu):
            for button in account.menu.buttons.all():
                if message.text == button.text:
                    message.type = MessageType.BUTTON

        return message

    def process_message(self, message: Message, account: Account):
        """
        Process the message with a bound handler.
        :param message: bot_engine.Massage object
        :param account: bot_engine.Account object
        :return: None
        """
        if self.handler:
            self.call_handler(message, account)

    @property
    def call_handler(self) -> Callable:
        # importing handler or hot reloading
        if not hasattr(self, '_handler') or self.handler != self._old_handler:
            self._handler = import_string(self.handler)
            self._old_handler = self.handler
        return self._handler

    def enable_webhook(self):
        url = reverse('bot_engine:webhook', kwargs={'hash': self.token_hash})
        return self.api.enable_webhook(url=f'https://{DOMAIN}{url}')

    def disable_webhook(self):
        return self.api.disable_webhook()

    @property
    def api(self) -> BaseMessenger:
        if not hasattr(self, '_api'):
            url = self.logo
            self._api = self._api_class(
                self.token, proxy=self.proxy, name=self.title,
                avatar=f'https://{DOMAIN}{url}'
            )
        return self._api

    @property
    def _api_class(self) -> Type[BaseMessenger]:
        """
        Returns the connector class of selected type.
        """
        return MessengerType(self.api_type).messenger_class


class AccountManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('user', 'messenger', 'menu')


class Account(models.Model):
    id = models.CharField(
        _('account id'), max_length=256,
        primary_key=True, editable=False)
    username = models.CharField(
        _('user name'), max_length=256,
        null=True, blank=True)
    utm_source = models.CharField(
        _('utm source'), max_length=256,
        null=True, blank=True)
    info = JSONField(
        _('information'),
        default=dict, blank=True)
    context = JSONField(
        _('context'),
        default=dict, blank=True)
    phone = models.CharField(
        _('phone'), max_length=20,
        null=True, blank=True)

    messenger = models.ForeignKey(
        'Messenger', models.SET_NULL,
        verbose_name=_('messenger'), related_name='accounts',
        null=True, blank=True)
    menu = models.ForeignKey(
        'Menu', models.SET_NULL,
        verbose_name=_('current menu'), related_name='accounts',
        null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, models.SET_NULL,
        verbose_name=_('user'), related_name='accounts',
        null=True, blank=True)

    is_active = models.BooleanField(
        _('active'),
        default=False, editable=False,
        help_text=_('This flag changes when the user account on '
                    'the messenger API server is subscribed/unsubscribed.'))
    updated = models.DateTimeField(
        _('last visit'), auto_now=True)
    created = models.DateTimeField(
        _('first visit'), auto_now_add=True)

    objects = AccountManager()

    class Meta:
        verbose_name = _('account')
        verbose_name_plural = _('accounts')
        unique_together = ('id', 'messenger')

    def __str__(self):
        return self.username or self.id

    def __repr__(self):
        return f'<bot_engine.Account object ({self.id})>'

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()

    @property
    def avatar(self) -> str:
        return self.info.get('avatar') or ''

    def send_message(self, message: Message,
                     buttons: List[Button] = None,
                     i_buttons: List[Button] = None):
        # TODO simplify
        if buttons:
            message.buttons = message.buttons or [] + buttons
        if i_buttons:
            message.buttons = message.buttons or [] + list(i_buttons)
        if self.menu:
            message.buttons = message.buttons or [] + self.menu.button_list()
            message.buttons = message.buttons or [] + self.menu.i_button_list()

        # TODO: make Massage parameter and handle him in api objects
        try:
            self.messenger.api.send_message(self.id, message)
        except NotSubscribed:
            self.is_active = False
            log.warning(f'Account {self.username}:{self.id} is not subscribed.')
        except MessengerException as err:
            log.exception(err)

    def update_info(self):
        try:
            user_info = self.messenger.api.get_user_info(self.id,
                                                         chat_id=self.id)
            self.update(username=user_info.get('username'),
                        info=user_info.get('info'))
        except RequestsLimitExceeded as err:
            self.info['error'] = str(err)
            # self.update(username=message.sender.username,
            #             info=requestLimit)
            log.exception(err)


class Menu(models.Model):
    title = models.CharField(
        _('title'), max_length=256)
    message = models.CharField(
        _('message'), max_length=1024,
        null=True, blank=True,
        help_text=_('The text of the message sent when you get to this menu. '
                    'If empty, nothing is sent.'))
    comment = models.CharField(
        _('comment'), max_length=1024,
        null=True, blank=True,
        help_text=_('Comment text. Does not affect functionality.'))
    handler = models.CharField(
        _('handler'), max_length=256,
        default='', blank=True,
        help_text=_(f'Your handler implementation must implement '
                    f'the {ECHO_HANDLER} interface.'))

    buttons = SortedManyToManyField(
        'Button', blank=True,
        sort_value_field_name='order',
        verbose_name=_('buttons'), related_name='menus')

    updated = models.DateTimeField(
        _('updated'), auto_now=True)
    created = models.DateTimeField(
        _('created'), auto_now_add=True)

    class Meta:
        verbose_name = _('menu')
        verbose_name_plural = _('menus')
        unique_together = ('title', )

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'<bot_engine.Menu object ({self.id})>'

    def process_message(self, message: Message, account: Account):
        """
        Process the message with a bound handler.
        :param message: new incoming massage object
        :param account: message sender object
        :return: None
        """
        # TODO check process
        # TODO make permissions filter
        if message.is_button:
            buttons = self.buttons.filter(Q(command=message.text) |
                                          Q(text=message.text)).all()
            if len(buttons) == 0:
                buttons = Button.objects.filter(Q(command=message.text) |
                                                Q(text=message.text)).all()

            if buttons:
                return buttons[0].process_button(message, account)

            if not buttons or len(buttons) > 1:
                log.warning('The number of buttons found is different from one.'
                            ' This can lead to unplanned behavior.'
                            ' We recommend making the buttons unique.')
        elif self.handler:
            self.call_handler(message, account)

    @property
    def call_handler(self) -> Callable:
        if not hasattr(self, '_handler'):
            self._handler = import_string(self.handler)
        return self._handler

    def button_list(self) -> List[Button]:
        return list(self.buttons.filter(is_inline=False).all())

    def i_button_list(self) -> List[Button]:
        return list(self.buttons.filter(is_inline=True).all())


class Button(models.Model):
    title = models.CharField(
        _('title'), max_length=256)
    text = models.CharField(
        _('text'), max_length=256,
        help_text=_('Button text displayed.'))
    message = models.CharField(
        _('message'), max_length=1024,
        null=True, blank=True,
        help_text=_('The text of the message sent during the processing of '
                    'a button click. If empty, nothing is sent.'))
    comment = models.CharField(
        _('comment'), max_length=1024,
        null=True, blank=True,
        help_text=_('Comment text. Does not affect functionality.'))

    handler = models.CharField(
        _('handler'), max_length=256,
        default='', blank=True,
        help_text=_(f'Your handler implementation must implement '
                    f'the {BUTTON_HANDLER} interface.'))
    next_menu = models.ForeignKey(
        'Menu', models.SET_NULL,
        verbose_name=_('next menu'), related_name='from_buttons',
        null=True, blank=True)
    for_staff = models.BooleanField(
        _('for staff users'),
        default=False, blank=True,
        help_text=_('Buttons with this flag are available only for user '
                    'accounts of site staff (django.contrib.auth).'))
    for_admin = models.BooleanField(
        _('for admin users'),
        default=False, blank=True,
        help_text=_('Buttons with this flag are available only for user '
                    'accounts of site admins (django.contrib.auth).'))

    command = models.CharField(
        _('command'), max_length=256,
        default='', editable=False)
    is_inline = models.BooleanField(
        _('inline'), default=False,
        help_text=_('Inline in message.'))
    is_active = models.BooleanField(
        _('active'), default=True)
    updated = models.DateTimeField(
        _('updated'), auto_now=True)
    created = models.DateTimeField(
        _('created'), auto_now_add=True)

    class Meta:
        verbose_name = _('button')
        verbose_name_plural = _('buttons')
        unique_together = ('command', )

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'<bot_engine.Button object ({self.command})>'

    def process_button(self, message: Message, account: Account):
        """
        Process the message with a bound handler.
        :param message: new incoming massage object
        :param account: message sender object
        :return: None
        """
        # TODO check process
        if self.message:
            account.send_message(Message.text(self.message))

        if self.next_menu:
            account.update(menu=self.next_menu)

            btn_list = list(self.next_menu.buttons.all()) or None
            if self.next_menu.message:
                msg_text = self.next_menu.message
                account.send_message(Message.text(msg_text), buttons=btn_list)
            else:
                account.send_message(Message.keyboard(btn_list))

        if self.handler:
            self.call_handler(message, account)

    @property
    def call_handler(self) -> Callable:
        if not hasattr(self, '_handler'):
            self._handler = import_string(self.handler)
        return self._handler

    def save(self, *args, **kwargs):
        if not self.command:
            rnd = uuid4().hex[::3]
            self.command = f'btn-{slugify(self.title)}-{rnd}'
        super().save(*args, **kwargs)

    @property
    def action(self) -> str:
        return self.handler or str(self.next_menu)

    def to_dict(self) -> dict:
        return {'text': self.title,
                'command': self.command,
                'size': (2, 1), }
