# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022


from . import Message
from .is_anon import is_anon


def is_private(data: Message, group: bool = False) -> bool:

    """Is private (PM or group) or not"""

    if is_anon(data):
        return False

    if not group:
        if hasattr(data, "user_added"):
            return False

        return data.sender.id == data.chat.id

    if data.sender.id == data.chat.id:
        return False

    if hasattr(data.chat, "username"):
        return bool(not data.chat.username)
    return True

