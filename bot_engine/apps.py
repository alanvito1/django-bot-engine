from django.apps import AppConfig


class BotEngineConfig(AppConfig):
    name = 'bot_engine'
    label = 'bot_engine'
    verbose_name = 'Django Bot Engine'

    # def ready(self):
    #     # TODO implement autodiscover handlers
    #     self.module.autodiscover('bot_handlers')
