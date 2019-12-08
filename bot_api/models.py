import logging
from hashlib import md5
from typing import List, Type

from django.contrib.sites.models import Site
from django.db import models
from django.urls import reverse
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

from config import bot_handler
from .errors import BotApiError
from .imconnectors.imconnector import IMConnector
from .imconnectors import Telegram, Viber
from .types import Button


__all__ = ('Messenger', 'Menu', 'MenuItem')

log = logging.getLogger(__name__)
DEFAULT_BOT = 'bot_api.chatbots.EchoBot'


class Menu(models.Model):
    title = models.CharField(
        _('title'), max_length=128)
    text = models.CharField(
        _('text'), max_length=1024)
    comment = models.CharField(
        _('comment'), max_length=1024,
        null=True, blank=True)

    parent = models.ForeignKey(
        'self', models.CASCADE,
        related_name='children',
        null=True, blank=True)

    class Meta:
        verbose_name = _('menu')
        verbose_name_plural = _('menus')

    def __str__(self):
        return self.title

    def root_menu(self):
        return self

    def as_button_list(self) -> List[Button]:
        return [item.as_button() for item in self.items.all()]


class MenuItem(models.Model):
    title = models.CharField(
        _('title'), max_length=128)
    cmd = models.CharField(
        _('command'), max_length=128)
    handler_method = models.CharField(
        _('handler'), max_length=256,
        default='', null=True, blank=True,
        help_text=_('Your chatbot class method that implements '
                    'the interface "item_handler".'))

    menu = models.ForeignKey(
        Menu, models.CASCADE,
        related_name='items')
    next_menu = models.ForeignKey(
        Menu, models.CASCADE,
        related_name='from_item',
        null=True, blank=True)

    is_active = models.BooleanField(
        _('active'), default=True)
    # This flag indicates that the menu item is at the testing stage and
    #  it is not advisable to display it to users.
    is_test = models.BooleanField(
        _('test function'), default=True,
        help_text=_('This flag hides the item from ordinary users. '
                    'The item is visible only to users with '
                    'the <i>is_admin</i> flag.'))
    comment = models.CharField(
        _('comment'), max_length=1024,
        null=True, blank=True)

    class Meta:
        verbose_name = _('menu item')
        verbose_name_plural = _('menu items')
        unique_together = ('cmd', )

    def __str__(self):
        return self.title

    @property
    def command(self) -> str:
        return 'MI_' + self.cmd

    @property
    def action(self) -> str:
        return self.handler_method or str(self.next_menu)

    def as_button(self) -> Button:
        return Button(self.title, self.command, size=(2, 1))


class Messenger(models.Model):
    _api = None
    _bot = None

    NONE = 'nn'
    MESSENGER = 'mg'
    SKYPE = 'sk'
    SLACK = 'sl'
    TELEGRAM = 'tg'
    VIBER = 'vb'
    WECHAT = 'wc'
    WHATSAPP = 'wa'
    _choices = (
        (NONE, 'None'), (MESSENGER, 'FB Messenger'), (SKYPE, 'Skype'),
        (SLACK, 'Slack'), (TELEGRAM, 'Telegram'), (VIBER, 'Viber'),
        (WECHAT, 'WeChat'), (WHATSAPP, 'WhatsApp'), )
    _connector_classes = {
        TELEGRAM: Telegram,
        VIBER: Viber, }
    _handler_choices = ((x, x) for x in bot_handler.chatbots.keys())

    title = models.CharField(
        _('title'), max_length=128)
    api_type = models.CharField(
        _('API type'), max_length=2,
        choices=_choices)
    handler_class = models.CharField(
        _('bot class'), max_length=256,
        # choices=_handler_choices,
        default=DEFAULT_BOT,
        help_text=_('Your chatbot class that implements '
                    'the interface "bot_api.chatbots.BaseBot".'))
    token = models.CharField(
        _('bot token'), max_length=128,
        null=True, blank=True)
    proxy = models.CharField(
        _('proxy'), max_length=256,
        default='', blank=True,
        help_text=_('Enter proxy uri with format '
                    '"schema://user:password@proxy_address:port"'))

    enabled = models.BooleanField(
        _('enabled'), default=False,
        editable=False,
        help_text=_('This flag changes when webhook is activated/deactivated.'))
    hash = models.CharField(
        _('token hash'), max_length=128,
        default='', editable=False)
    menu = models.ForeignKey(
        Menu, models.CASCADE, null=True, blank=True,
        related_name='messengers')

    class Meta:
        verbose_name = _('messenger')
        verbose_name_plural = _('messengers')
        ordering = ('title', 'api_type')
        unique_together = ('token', 'api_type')

    def __str__(self):
        return '%s (%s)' % (self.title, self.api_type)

    def get_absolute_url(self):
        return reverse('bot_api:detail',
                       kwargs={'api_type': self.api_type, 'id': self.id})

    def get_webhook_enable_url(self):
        return reverse('bot_api:enable',
                       kwargs={'api_type': self.api_type, 'id': self.id})

    def get_webhook_disable_url(self):
        return reverse('bot_api:disable',
                       kwargs={'api_type': self.api_type, 'id': self.id})

    def get_token_hash(self) -> str:
        if not self.hash:
            self.hash = md5(self.token.encode()).hexdigest()
            self.save()
        return self.hash

    @property
    def api(self) -> IMConnector:
        if self._api is None:
            self._api = self._api_class(
                token=self.token, proxy=self.proxy, name=self.title,
                avatar_url='https://mediaserver.xyz/static/img/logo.jpg')
        return self._api

    @property
    def bot(self):  # -> BaseBot
        # TODO: after called save method need change bot class
        if self._bot is None:
            if self.handler_class:
                self._bot = import_string(self.handler_class)(self.api)
            else:
                self.handler_class = DEFAULT_BOT
                self._bot = import_string(DEFAULT_BOT)(self.api)
        return self._bot

    def enable_webhook(self):
        webhook_url = 'https://{host}{url}'.format(
            host=Site.objects.get_current().domain,
            url=reverse('bot_api:callback',
                        kwargs={'hash': self.get_token_hash()}))
        return self.api.enable_webhook(uri=webhook_url)

    def disable_webhook(self):
        return self.api.disable_webhook()

    @property
    def _api_class(self) -> Type[IMConnector]:
        """
        Returns the connector class of saved type.
        """
        return self._connector_classes.get(self.api_type, IMConnector)
