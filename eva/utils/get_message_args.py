# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022


from . import Message


def get_message_args(message: Message) -> list[str]:

    """
    get_message_args('/say hello world') will return
    ['hello', 'world']

    """

    args: list[str] = message.text.split(" ")[1:]
    return [] if not args else args
