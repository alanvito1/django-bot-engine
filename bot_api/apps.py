from django.apps import AppConfig


class BotAPIConfig(AppConfig):
    name = 'bot_api'
    verbose_name = 'Django Bot API'

    # def ready(self):
    #     # ?
    #     BOT_API_CLIENT_MODEL = ''
    #     scan_apps_chatbots()
