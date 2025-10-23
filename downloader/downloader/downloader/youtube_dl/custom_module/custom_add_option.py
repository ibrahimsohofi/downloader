#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

__all__ = ['add_verbosity_group_option']


def add_verbosity_group_option(verbosity):
    '''添加选项构造器verbosity组的选项'''
    verbosity.add_option(
        '--call-custom',
        dest='get_call_custom', action='store_true',
        default=False,
        help='call custom module'
    )
    verbosity.add_option(
        '--call-cookie-str',
        dest='get_cookie_str',
        metavar='pass login cookie',
        default='',
        help='''call login cookie''')
