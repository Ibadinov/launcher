#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='watchdog',
    version='0.1.7',
    url='http://github.com/Ibadinov/watchdog',
    license='MIT',
    author='Marat Ibadinov',
    author_email='ibadinov@me.com',

    platforms='any',
    dependency_links=['http://github.com/Ibadinov/ptime/tarball/master#egg=ptime-0.1.3'],
    install_requires=['ptime'],
    packages=['watchdog'],
    test_suite='tests'
)
