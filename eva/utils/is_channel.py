# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022


from . import Message


def is_channel(data: Message) -> bool:

    if hasattr(data.chat, "broadcast") and data.chat.broadcast:
        return True
    return False
