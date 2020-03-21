import json

from bot_engine.models import Account
from bot_engine.types import Message


def main_menu_echo(message: Message, account: Account):
    if account.context.get('reply'):
        message.reply_to_id = message.id
    account.send_message(message)


def submenu_text(message: Message, account: Account):
    answer = Message.text(text=f'This is a submenu handler. '
                               f'You sent me this message:')
    account.send_message(answer)
    account.send_message(message)


def button_context(message: Message, account: Account):
    answer = Message.text(text=json.dumps(account.context))
    account.send_message(answer)


def button_menu(message: Message, account: Account):
    answer = Message.text(text=str(account.menu))
    account.send_message(answer)


def button_answer_type(message: Message, account: Account):
    if account.context.get('reply'):
        account.context['reply'] = False
        account.save()
        account.send_message(Message.text('Reply disabled'))
    else:
        account.context['reply'] = True
        account.save()
        account.send_message(Message.text('Reply enabled'))
