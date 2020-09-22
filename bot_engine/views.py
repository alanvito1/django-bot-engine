import json
import logging

from django.http.request import HttpRequest
from django.http.response import (
    HttpResponse, HttpResponseNotFound, HttpResponseServerError,
)
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Messenger


log = logging.getLogger(__name__)


class MessengerSwitch(View):
    """
    View for activate and deactivate webhooks
    """
    @staticmethod
    def post(request: HttpRequest, **kwargs) -> HttpResponse:
        switch_on = kwargs.get('switch_on')
        msgr_id = kwargs.get('id')
        try:
            messenger = Messenger.objects.get(id=msgr_id)
        except Messenger.DoesNotExist as err:
            log.exception(f'Messenger not found; Id={msgr_id}; Error={err};')
            return HttpResponseNotFound('Handler not found.')

        if switch_on:
            messenger.enable_webhook()
        else:
            messenger.disable_webhook()

        return HttpResponse()


@method_decorator(csrf_exempt, 'dispatch')
class MessengerWebhook(View):
    """
    Endpoint for a Messenger's webhook
    """
    @staticmethod
    def post(request: HttpRequest, **kwargs) -> HttpResponse:
        log.debug(f'Bot Engine Webhook; Request content={request.body};')
        im_hash = kwargs.get('hash', '')

        try:
            messenger = Messenger.objects.get(hash=im_hash)
            answer = messenger.dispatch(request)
            if answer is not None:
                answer = json.dumps(answer).encode('utf-8')
                content_type = 'application/json'
                log.debug(f'Bot Engine Webhook; Response={answer};')
            else:
                answer, content_type = b'', None
        except Messenger.DoesNotExist as err:
            log.exception(f'Messenger not found; Hash={im_hash}; Error={err};')
            return HttpResponseNotFound('Webhook not found.')
        except Exception as err:
            log.exception(f'Bot Engine Webhook; Hash={im_hash}; Error={err};')
            return HttpResponseServerError('Server error.')

        return HttpResponse(answer, content_type=content_type)
