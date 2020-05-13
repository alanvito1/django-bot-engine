import logging

from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView

from .models import Messenger


log = logging.getLogger(__name__)


class MessengerSwitch(APIView):
    """
    View for activate and deactivate webhooks
    """
    @staticmethod
    def post(request: Request, **kwargs) -> Response:
        switch_on = kwargs.get('switch_on')
        messenger_id = kwargs.get('id')
        try:
            messenger = Messenger.objects.get(id=messenger_id)
        except Messenger.DoesNotExist as err:
            log.exception(err)
            raise NotFound('Handler not found.')

        if switch_on:
            messenger.enable_webhook()
        else:
            messenger.disable_webhook()

        return Response()


class MessengerWebhook(APIView):
    """
    Endpoint for a Messenger's webhook
    """
    permission_classes = (AllowAny, )
    renderer_classes = (JSONRenderer, )

    @staticmethod
    def post(request: Request, **kwargs) -> Response:
        log.debug(f'Bot Engine Webhook; Message={request.data};')
        im_hash = kwargs.get('hash', '')

        try:
            messenger = Messenger.objects.get(hash=im_hash)
            answer = messenger.dispatch(request)
        except Messenger.DoesNotExist as err:
            log.exception(f'Messenger not found; Hash={hash}; Error={err};')
            raise NotFound('Webhook not found.')
        except Exception as err:
            log.exception(f'Bot Engine Webhook; Error={err};')
            raise

        log.debug(f'Bot Engine Webhook; Answer={answer};')
        return Response(answer)
