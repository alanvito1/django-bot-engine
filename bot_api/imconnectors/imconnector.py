from typing import Any, Dict, List

from django.http import HttpRequest

from ..types import Button, Message


class IMConnector:
    """
    Base class for IM connector
    """

    def __init__(self, token: str, **kwargs):
        self.token = token

    def enable_webhook(self, uri: str, **kwargs):
        """
        Initialize IM webhook
        """
        raise NotImplementedError('This method must be implemented in a subclass.')

    def disable_webhook(self):
        """
        Uninitialize IM webhook
        """
        raise NotImplementedError('This method must be implemented in a subclass.')

    def get_account_info(self) -> Dict[str, Any]:
        """
        Account info from IM service
        """
        raise NotImplementedError('This method must be implemented in a subclass.')

    def get_user_info(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        User info from IM service
        """
        raise NotImplementedError('This method must be implemented in a subclass.')

    def parse_message(self, request: HttpRequest) -> Message:
        """
        Parse incoming message
        """
        raise NotImplementedError('This method must be implemented in a subclass.')

    def send_message(self, receiver: str, message: str,
                     button_list: List[Button] = None, **kwargs) -> str:
        """
        Send message method
        """
        raise NotImplementedError('This method must be implemented in a subclass.')

    @staticmethod
    def _proxy(proxy_host: str) -> Dict[str, str]:
        return {'https': proxy_host, 'http': proxy_host}
