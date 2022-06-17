# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022


from dataclasses import dataclass


@dataclass
class User:

    id: int = int()
    username: str = str()
    first_name: str = str()
    bio: str = str()
    blocked: bool = False
