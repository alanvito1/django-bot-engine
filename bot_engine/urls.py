from django.urls import path

from .views import MessengerSwitch, MessengerWebhook


app_name = 'bot_engine'

urlpatterns = [
    path('<int:id>/activate/', MessengerSwitch.as_view(),
         {'switch_on': True}, name='activate'),
    path('<int:id>/deactivate/', MessengerSwitch.as_view(),
         {'switch_on': False}, name='deactivate'),
    path('<str:hash>/', MessengerWebhook.as_view(), name='webhook'),
]
