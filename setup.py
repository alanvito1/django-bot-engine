#!/usr/bin/env python

from setuptools import setup


setup(
    name='django-bot-api',
    version='0.1.0',
    description='Django application for creating bots for different chat platforms.',
    url='https://github.com/terentjew-alexey/django-bot-api',
    license='Apache 2.0',
    author='Aleksey Terentyev',
    author_email='terentjew.alexey@gmail.com',
    packages=['bot_api', 'bot_api.imconnectors'],
    install_requires=[
        'urllib3',
        'PySocks',
        'requests',
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Django',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Environment :: Other Environment',
        'Operating System :: OS Independent',
        'Topic :: Communications',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries'
    ]
)
