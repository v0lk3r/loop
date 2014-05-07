#!/usr/bin/env python
#! -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='Loop',
    version='0.1.1',
    packages=['loop'],
    install_requires=['python-inotify==0.6-test'],
    entry_points={
        'console_scripts': [
            'loop=loop.loop:main',
        ],
    },
    author='Volker Haas',
    author_email='volker.haas@gmail.com',
)
