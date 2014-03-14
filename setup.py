#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='launcher',
    version='0.1.16',
    url='http://github.com/Ibadinov/launcher',
    license='MIT',
    author='Marat Ibadinov',
    author_email='ibadinov@me.com',

    platforms='any',
    dependency_links=['http://github.com/Ibadinov/ptime/tarball/master#egg=ptime-0.1.4'],
    install_requires=['ptime>0.1.3'],
    packages=['launcher'],
    test_suite='tests'
)
