#!/usr/bin/env python
from setuptools import setup

from bot_engine import __version__


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
    packages=['bot_engine', 'bot_engine.messengers'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Django',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
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
