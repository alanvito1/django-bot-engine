import logging

from django import forms
from django.contrib import admin
from django.forms.widgets import Select
from django.template.defaultfilters import pluralize
from django.utils.translation import ugettext_lazy as _

from config import bot_handler
from .models import Menu, MenuItem, Messenger


log = logging.getLogger(__name__)


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent')
    list_filter = ('parent', )
    search_fields = ('title', 'text', 'comment')

    class Meta:
        model = Menu


# class MenuItemSelectWidget(Select):
#     """
#     Widget that lets you choose between chatbot classes.
#     """
#     _choices = None
#
#     @staticmethod
#     def items_as_choices():
#         if len(bot_handler.chatbots) <= 1:
#             # TODO scan apps
#             pass
#         tasks = list(sorted(name for name in bot_handler.menu_handlers))
#         return (('', ''), ) + tuple(zip(tasks, tasks))
#
#     @property
#     def choices(self):
#         if self._choices is None:
#             self._choices = self.items_as_choices()
#         return self._choices
#
#     @choices.setter
#     def choices(self, _):
#         # ChoiceField.__init__ sets ``self.choices = choices``
#         # which would override ours.
#         pass
#
#
# class MenuItemChoiceField(forms.ChoiceField):
#     """
#     Field that lets you choose between chatbot classes.
#     """
#     widget = MenuItemSelectWidget
#
#     def valid_value(self, value):
#         return True
#
#
# class MenuItemForm(forms.ModelForm):
#     """
#     Form that lets you create and modify periodic tasks.
#     """
#     handler_method = MenuItemChoiceField(
#         label=_('handler'),
#         required=False)
#
#     class Meta:
#         model = MenuItem
#         exclude = ()


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    # form = MenuItemForm

    list_display = ('title', 'menu', 'action', 'is_test', 'is_active')
    list_filter = ('is_active', 'menu', 'is_test')
    search_fields = ('title', 'command', 'handler_method', 'comment')

    class Meta:
        model = MenuItem


# class ChatbotSelectWidget(Select):
#     """
#     Widget that lets you choose between chatbot classes.
#     """
#     _choices = None
#
#     @staticmethod
#     def chatbots_as_choices():
#         if len(bot_handler.chatbots) <= 1:
#             # TODO scan apps
#             pass
#         tasks = list(sorted(name for name in bot_handler.chatbots))
#         return (('', ''), ) + tuple(zip(tasks, tasks))
#
#     @property
#     def choices(self):
#         if self._choices is None:
#             self._choices = self.chatbots_as_choices()
#         return self._choices
#
#     @choices.setter
#     def choices(self, _):
#         # ChoiceField.__init__ sets ``self.choices = choices``
#         # which would override ours.
#         pass
#
#
# class ChatbotChoiceField(forms.ChoiceField):
#     """
#     Field that lets you choose between chatbot classes.
#     """
#     widget = ChatbotSelectWidget
#
#     def valid_value(self, value):
#         return True
#
#
# class MessengerForm(forms.ModelForm):
#     """
#     Form that lets you create and modify periodic tasks.
#     """
#     handler = ChatbotChoiceField(
#         label=_('Chatbot handler'),
#         required=False, )
#
#     class Meta:
#         model = Messenger
#         exclude = ()
#
#     # def clean(self):
#     #     data = super().clean()
#     #     handler_class = data.get('handler_class')
#     #     return data


@admin.register(Messenger)
class MessengerAdmin(admin.ModelAdmin):
    # form = MessengerForm

    list_display = ('__str__', 'handler_class', 'enabled', 'proxy')
    list_display_links = ('__str__', )
    list_filter = ('api_type', 'enabled')
    search_fields = ('title', 'api_type')
    readonly_fields = ('enabled', 'hash')
    actions = ('enable_webhook', 'disable_webhook')
    fieldsets = (
        (None, {
            'fields': ('title', 'api_type', 'handler_class'),
            'classes': ('extrapretty', 'wide'),
        }),
        (None, {
            'fields': ('enabled', ),
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
            for im in queryset.all():
                im.enable_webhook()
            rows_updated = queryset.update(enabled=True)
            self.message_user(request,
                              _('{0} messenger{1} {2} successfully enabled')
                              .format(rows_updated, pluralize(rows_updated),
                                      pluralize(rows_updated, _('was,were'))))
        except Exception as err:
            log.exception(err)
    enable_webhook.short_description = _('Enable webhook selected messengers')

    def disable_webhook(self, request, queryset):
        for im in queryset.all():
            im.disable_webhook()
        rows_updated = queryset.update(enabled=False)
        self.message_user(request,
                          _('{0} messenger{1} {2} successfully disabled')
                          .format(rows_updated, pluralize(rows_updated),
                                  pluralize(rows_updated, _('was,were'))))
    disable_webhook.short_description = _('Disable webhook selected messengers')
