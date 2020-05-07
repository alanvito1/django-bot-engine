import logging

from django import forms
from django.contrib import admin
from django.forms.widgets import Select
from django.template.defaultfilters import pluralize
from django.utils.translation import gettext_lazy as _

from . import bot
from .models import Messenger, Account, Menu, Button
from .types import Message


log = logging.getLogger(__name__)


class HandlerSelectWidget(Select):
    """
    Widget that lets you choose between chatbot handlers functions.
    """
    _choices = None

    @staticmethod
    def handlers_as_choices():
        handlers = list(sorted(name for name in bot.handlers.keys()))
        return (('', ''), ) + tuple(zip(handlers, handlers))

    @property
    def choices(self):
        if self._choices is None:
            self._choices = self.handlers_as_choices()
        return self._choices

    @choices.setter
    def choices(self, _):
        # ChoiceField.__init__ sets ``self.choices = choices``
        # which would override ours.
        pass


class HandlerChoiceField(forms.ChoiceField):
    """
    Field that lets you choose between chatbot handlers.
    """
    widget = HandlerSelectWidget

    def valid_value(self, value):
        return True


class MessengerForm(forms.ModelForm):
    """
    Form that lets you create and modify messenger accounts.
    """
    handler_list = HandlerChoiceField(
        label=_('Handler (registered)'),
        required=False, )
    handler = forms.CharField(
        label=_('Handler (custom)'),
        required=False, )

    class Meta:
        model = Messenger
        exclude = ()

    def clean(self):
        data = super().clean()
        selected_handler = data.get('handler_list')

        if selected_handler:
            data['handler'] = selected_handler
        if not data['handler']:
            data['handler'] = ''
            # exc = forms.ValidationError(_('Need name of handler'))
            # self._errors['handler'] = self.error_class(exc.messages)
            # raise exc

        return data


@admin.register(Messenger)
class MessengerAdmin(admin.ModelAdmin):
    """
    Admin-interface for messenger accounts.
    """
    form = MessengerForm

    list_display = ('title', 'api_type', 'menu', 'proxy', 'is_active')
    list_filter = ('api_type', 'menu', 'is_active', 'updated')
    search_fields = ('title', 'api_type', 'token', 'hash')
    readonly_fields = ('is_active', 'hash')
    actions = ('enable_webhook', 'disable_webhook')
    fieldsets = (
        (None, {
            'fields': ('title', 'api_type', 'is_active', 'handler_list',
                       'handler', 'welcome_text', 'menu', 'logo'),
            'classes': ('extrapretty', 'wide'),
        }),
        (_('Authenticate'), {
            'fields': ('token', ),
            'classes': ('extrapretty', 'wide'),
        }),
        (_('Proxy'), {
            'fields': ('proxy', ),
            'classes': ('extrapretty', 'wide', 'collapse', 'in'),
        })
    )

    class Meta:
        model = Messenger

    def enable_webhook(self, request, queryset):
        try:
            for messenger in queryset.all():
                messenger.enable_webhook()
            rows_updated = queryset.update(is_active=True)
            msg = _(f'{rows_updated} messenger{pluralize(rows_updated)} '
                    f'{pluralize(rows_updated, _("was,were"))} '
                    f'successfully enabled')
            self.message_user(request, msg)
        except Exception as err:
            log.exception(err)
    enable_webhook.short_description = _('Enable webhook selected messengers')

    def disable_webhook(self, request, queryset):
        for messenger in queryset.all():
            messenger.disable_webhook()
        rows_updated = queryset.update(is_active=False)
        msg = _(f'{rows_updated} messenger{pluralize(rows_updated)} '
                f'{pluralize(rows_updated, _("was,were"))} '
                f'successfully disabled')
        self.message_user(request, msg)
    disable_webhook.short_description = _('Disable webhook selected messengers')


# class AccountForm(forms.ModelForm):
#     """
#     Form that lets you create and modify chatbot handlers.
#     """
#     def _clean_json(self, field):
#         value = self.cleaned_data[field]
#
#         try:
#             json.loads(value)
#         except ValueError as exc:
#             raise forms.ValidationError(
#                 _('Unable to parse JSON: %s') % exc,
#             )
#
#         return value
#
#     def clean_context(self):
#         return self._clean_json('context')


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """
    Admin-interface for user messenger accounts.
    """
    list_display = ('__str__', 'messenger', 'menu', 'user',
                    'utm_source', 'is_active', 'updated')
    list_filter = ('messenger', 'utm_source', 'is_active', 'updated', 'created')
    search_fields = ('id', 'username', 'utm_source')
    readonly_fields = ('id', 'info', 'messenger',
                       'is_active', 'updated', 'created')
    actions = ('send_ping', 'update_info')
    fieldsets = (
        (None, {
            'fields': ('id', 'messenger', 'is_active', 'username', 'user'),
            'classes': ('extrapretty', 'wide'),
        }),
        (_('Info'), {
            'fields': ('info', 'menu', 'context', 'phone', 'utm_source',
                       'updated', 'created'),
            'classes': ('extrapretty', 'wide'),
        })
    )

    class Meta:
        model = Account

    def send_ping(self, request, queryset):
        # TODO: implement checking subscription or ping message (mb. user_info?)
        for account in queryset:
            account.send_message(Message.text('ping'))
    send_ping.short_description = _('Send ping')

    def update_info(self, request, queryset):
        for account in queryset:
            account.update_info()
    update_info.short_description = _('Update info')


class MenuForm(forms.ModelForm):
    """
    Form that lets you create and modify chatbot menus.
    """
    handler_list = HandlerChoiceField(
        label=_('Handler (registered)'),
        required=False, )
    handler = forms.CharField(
        label=_('Handler (custom)'),
        required=False, )

    class Meta:
        model = Menu
        exclude = ()

    def clean(self):
        data = super().clean()
        selected_handler = data.get('handler_list')

        if selected_handler:
            data['handler'] = selected_handler
        if not data['handler']:
            data['handler'] = ''

        return data


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    """
    Admin-interface for chatbot menus.
    """
    form = MenuForm

    list_display = ('title', 'message', 'comment', 'updated')
    list_filter = ('updated', 'created')
    search_fields = ('title', 'message', 'comment', 'handler')
    # filter_horizontal = ('buttons', )  # used sortedm2m
    fieldsets = (
        (None, {
            'fields': ('title', 'message', 'comment',
                       'handler_list', 'handler', 'buttons'),
            'classes': ('extrapretty', 'wide'),
        }),
    )

    class Meta:
        model = Menu


class ButtonHandlerSelectWidget(HandlerSelectWidget):
    """
    Widget that lets you choose between chatbot button handlers functions.
    """
    @staticmethod
    def handlers_as_choices():
        handlers = list(sorted(name for name in bot.button_handlers.keys()))
        return (('', ''), ) + tuple(zip(handlers, handlers))


class ButtonHandlerChoiceField(forms.ChoiceField):
    """
    Field that lets you choose between chatbot button handlers.
    """
    widget = ButtonHandlerSelectWidget

    def valid_value(self, value):
        return True


class ButtonForm(forms.ModelForm):
    """
    Form that lets you create and modify chatbot buttons.
    """
    handler_list = ButtonHandlerChoiceField(
        label=_('Handler (registered)'),
        required=False, )
    handler = forms.CharField(
        label=_('Handler (custom)'),
        required=False, )

    class Meta:
        model = Button
        exclude = ()

    def clean(self):
        data = super().clean()
        selected_handler = data.get('handler_list')

        if selected_handler:
            data['handler'] = selected_handler
        if not data['handler']:
            data['handler'] = ''

        return data


@admin.register(Button)
class ButtonAdmin(admin.ModelAdmin):
    """
    Admin-interface for chatbot buttons.
    """
    form = ButtonForm

    list_display = ('title', 'text', 'comment', 'next_menu',
                    'is_inline', 'for_staff', 'for_admin', 'is_active')
    list_filter = ('is_inline', 'for_staff', 'for_admin', 'is_active')
    search_fields = ('title', 'text', 'message', 'comment', 'command')
    readonly_fields = ('command', )
    fieldsets = (
        (None, {
            'fields': ('title', 'text', 'command', 'message', 'comment',
                       'handler_list', 'handler', 'next_menu',
                       ('for_staff', 'for_admin'), ('is_inline', 'is_active')),
            'classes': ('extrapretty', 'wide'),
        }),
    )

    class Meta:
        model = Button
