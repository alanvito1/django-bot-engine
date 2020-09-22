from typing import Any, Dict, List, Optional, Union

from django.http.request import HttpRequest

from ..types import Message


class BaseMessenger:
    """
    Base class for IM connector
    """

    def __init__(self, token: str, **kwargs):
        self.token = token
        self.proxy_addr = self._proxy(kwargs.get('proxy'))
        self.name = kwargs.get('name')
        self.avatar_url = kwargs.get('avatar')

    def enable_webhook(self, url: str, **kwargs):
        """
        Activate IM bot webhook
        :param url: webhook url
        :param kwargs:
        :return: None or response from api
        """
        raise NotImplementedError('`enable_webhook()` must be implemented.')

    def disable_webhook(self):
        """
        Deactivate IM bot webhook
        :return: None or response from api
        """
        raise NotImplementedError('`disable_webhook()` must be implemented.')

    def get_account_info(self) -> Dict[str, Any]:
        """
        Account info from IM API
        :return: dict with account info
        """
        raise NotImplementedError('`get_account_info()` must be implemented.')

    def get_user_info(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        User info from IM API
        :type user_id: user id
        :return: dict with user info
        """
        raise NotImplementedError('`get_user_info()` must be implemented.')

    def parse_message(self, request: HttpRequest) -> Message:
        """
        Parse incoming message
        :param request: Django HttpRequest object
        :return: Message object
        """
        raise NotImplementedError('`_parse_message()` must be implemented.')

    def send_message(self, receiver: str,
                     messages: Union[Message, List[Message]]) -> List[str]:
        """
        Send message method
        :param receiver: receiver user id
        :param messages: Message object or list of Message objects
        :return: message id list
        """
        raise NotImplementedError('`send_message()` must be implemented.')

    def welcome_message(self, text: str) -> Union[str, Dict[str, Any], None]:
        """
        Return message object method
        :param text: message text
        :return: api message object
        """
        return None

    @staticmethod
    def _proxy(proxy_url: Optional[str]) -> Optional[Dict[str, str]]:
        if proxy_url:
            return {'https': proxy_url, 'http': proxy_url}
        return None
