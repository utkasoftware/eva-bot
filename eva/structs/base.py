# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022


class BaseStruct:
    """
    Base minimal struct generator from dicts

    >>> args = {'foo': 1, 'bar': 2}
    >>> u = BaseStruct(**args)
    >>> u.foo
    1
    >>> u.bar
    2
    """

    def __init__(this, **data):

        this.__dict__.update(data)
