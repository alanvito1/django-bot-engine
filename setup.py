#!/usr/bin/env python
from setuptools import setup

exec(open('bot_engine/__init__.py').read())


setup(
    name='django-bot-engine',
    version=__version__,
    description='Django application for creating bots for different chat platforms.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/terentjew-alexey/django-bot-engine',
    license='Apache License 2.0',
    author='Aleksey Terentyev',
    author_email='terentjew.alexey@gmail.com',
    install_requires=open('requirements.txt').readlines(),
    packages=['bot_engine', 'bot_engine.messengers', 'bot_engine.migrations'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Django',
        'Framework :: Django :: 3.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Environment :: Other Environment',
        'Operating System :: OS Independent',
        'Topic :: Communications',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries'
    ]
)
