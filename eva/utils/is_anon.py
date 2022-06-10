# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022


from . import Message


def is_anon(data: Message) -> bool:

    """Check for anonymous admin"""
    if hasattr(data.peer_id, "channel_id") and data.sender is None:
        return bool(data.peer_id.channel_id == data.chat.id)
    return False
