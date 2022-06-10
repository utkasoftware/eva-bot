# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022


from dataclasses import dataclass


@dataclass
class Captcha:

    text: str = str()
    image: object = object()
    width: int = int()
    height: int = int()
    length: int = int()
    found: bool = bool()
    error: bool = bool()
    error_msg: str = str()
    expired: bool = bool()
    accepted: bool = bool()
    for_chat: int = int()
    created_at: str = str()
