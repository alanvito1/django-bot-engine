

class BotApiError(Exception):
    """
    Bot API exception class
    """


class MessengerException(BotApiError):
    """
    Instant Messenger exception class
    """


class RequestsLimitExceeded(BotApiError):
    """
    Exception class a Request limit exceeded
    """


class NotSubscribed(BotApiError):
    """
    Exception class a Account not subscribed
    """
