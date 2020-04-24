import logging
from collections import defaultdict

from django.utils.module_loading import autodiscover_modules


__title__ = 'Django bot api'
__version__ = '0.1.1'
__author__ = 'Aleksey Terentyev'
__license__ = 'Apache License 2.0'
__copyright__ = 'Copyright 2019-2020 Aleksey Terentyev'


default_app_config = 'bot_engine.apps.BotEngineConfig'
log = logging.getLogger(__name__)


def autodiscover():
    autodiscover_modules('bot_handlers')


class HandlerRegistry:
    """"""
    def __init__(self):
        self._handlers = defaultdict(callable)
        self._button_handlers = defaultdict(callable)

    def handler(self, handler):
        self._handlers[f'{handler.__module__}.{handler.__name__}'] = handler

        return handler

    def button_handler(self, handler):
        self._button_handlers[f'{handler.__module__}.{handler.__name__}'] = handler

        return handler

    @property
    def handlers(self):
        return self._handlers

    @property
    def button_handlers(self):
        return self._button_handlers

#     def chatbot(self, cls):
#         wrapped_class = '%s:%s' % (cls.__module__, cls.__name__)
#         self._chatbot_classes[wrapped_class] = cls
#
#         log.debug('wrapped_class={};'.format(wrapped_class))
#         # class Wrapper(cls):
#         #     print(cls.__module__, cls.__name__)
#         #     return cls(*args, **kwargs)
#         return cls
#
#     def menu_item(self, func):
#         wrapped_function = '%s:%s' % (func.__module__, func.__name__)
#         self._menu_items[wrapped_function] = func
#
#         # @wraps(func)
#         # def wrapper(*args, **kwargs):
#         #     print(func.__module__, func.__name__)
#         #     return func(*args, **kwargs)
#         return func


bot = HandlerRegistry()
