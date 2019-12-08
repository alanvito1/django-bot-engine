from django.urls import path

from .views import MessengerCallback, MessengerSwitch


app_name = 'bot_api'

urlpatterns = [
    path('<str:api_type>/<int:id>/enable/',
         MessengerSwitch.as_view(), {'switch_on': True}, name='enable'),
    path('<str:api_type>/<int:id>/disable/',
         MessengerSwitch.as_view(), {'switch_on': False}, name='disable'),
    path('<str:hash>/', MessengerCallback.as_view(), name='callback'),
]
