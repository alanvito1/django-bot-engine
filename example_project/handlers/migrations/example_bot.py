# Generated by Django 3.0.5 on 2020-04-27 10:53

from django.db import migrations


def create_example_bot_menu(apps, schema_editor):
    """
    Create example menus and buttons for bot example
    """
    Menu = apps.get_model('bot_engine', 'Menu')
    Button = apps.get_model('bot_engine', 'Button')
    db_alias = schema_editor.connection.alias

    # Buttons
    about = Button.objects.using(db_alias).create(
        title='About', text='About',
        message='This is a test bot project that implements the main '
                'functionality of instant messaging services.\nThe code is '
                'here https://github.com/terentjew-alexey/django-bot-engine/tree/master/example_project',
        comment='About bot',
        command='btn-about')
    back = Button.objects.using(db_alias).create(
        title='Back', text='Back',
        message='Return to Sub-Menu #1',
        command='btn-back')
    context = Button.objects.using(db_alias).create(
        title='Context', text='Context',
        message='This is your context data:',
        comment='Displays account context information.',
        handler='handlers.bot_handlers.button_context',
        command='btn-context')
    exit = Button.objects.using(db_alias).create(
        title='Exit', text='Exit',
        comment='To main menu',
        command='btn-exit')
    menu_info = Button.objects.using(db_alias).create(
        title='Menu info', text='Menu',
        message='You are in this menu:',
        comment='It displays information about the current menu of the account.',
        handler='handlers.bot_handlers.button_menu',
        command='btn-menu_info')
    reply_type = Button.objects.using(db_alias).create(
        title='Reply type', text='Reply',
        handler='handlers.bot_handlers.button_answer_type',
        command='btn-reply_type')
    submenu1_btn = Button.objects.using(db_alias).create(
        title='Submenu #1', text='Submenu',
        message='...',
        comment='Go to submenu #1.',
        command='btn-submenu1_btn')
    submenu2_btn = Button.objects.using(db_alias).create(
        title='Submenu #2', text='Go deeper',
        comment='Go to submenu #2.',
        command='btn-submenu2_btn')

    # Menus
    main_menu = Menu.objects.using(db_alias).create(
        title='Main menu',
        message='You are in the Main menu',
        comment='Start menu',
        handler='handlers.bot_handlers.main_menu_echo', )
    main_menu.buttons.set([submenu1_btn, about, reply_type])
    sub_menu1 = Menu.objects.using(db_alias).create(
        title='Submenu #1',
        message='You are in the first level submenu',
        handler='handlers.bot_handlers.submenu_text', )
    sub_menu1.buttons.set([submenu2_btn, menu_info, context, exit])
    sub_menu2 = Menu.objects.using(db_alias).create(
        title='Submenu #2',
        message='You are in the second level submenu', )
    sub_menu2.buttons.set([menu_info, context, back, exit])

    # Add button targets
    back.next_menu = sub_menu1
    exit.next_menu = main_menu
    submenu1_btn.next_menu = sub_menu1
    submenu2_btn.next_menu = sub_menu2


def delete_example_bot_menu(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('bot_engine', '0001_initial')
    ]

    operations = [
        migrations.RunPython(create_example_bot_menu, delete_example_bot_menu),
    ]
