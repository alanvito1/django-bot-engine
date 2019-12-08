import logging

from django.contrib.auth.decorators import login_required
from django.http import (
    HttpResponse, HttpResponseBadRequest,
    HttpResponseNotFound
)
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from .models import Messenger


log = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class MessengerSwitch(View):
    """
    View for activate and deactivate webhooks
    """
    def post(self, **kwargs):
        switch_on = kwargs.get('switch_on')
        messenger_id = kwargs.get('id')
        try:
            messenger = Messenger.objects.get(id=messenger_id)
        except Messenger.DoesNotExist as err:
            log.exception(err)
            return HttpResponseNotFound()
        else:
            if switch_on:
                messenger.enable_webhook()
            else:
                messenger.disable_webhook()

        return HttpResponse()


@method_decorator(csrf_exempt, name='dispatch')
class MessengerCallback(View):
    """
    Messengers callbacks
    """
    @classmethod
    def as_view(cls, **initkwargs):
        """
        This method is overridden to avoid a rare error
        when not deactivating CSRF protection.
        """
        view = super().as_view(**initkwargs)
        view.csrf_exempt = True
        return view

    def post(self, request, **kwargs):
        log.debug('Bot Api POST; '
                  'Message={};'.format(request.body.decode('utf-8')))
        im_hash = kwargs.get('hash', '')

        try:
            messenger = Messenger.objects.get(hash=im_hash)
            messenger.bot.dispatch(request)
        except Messenger.DoesNotExist as err:
            log.exception('Callback with this address was not found. '
                          'Error={}'.format(err))
            return HttpResponseBadRequest('Handler not found.')

        return HttpResponse()
