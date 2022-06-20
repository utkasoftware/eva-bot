# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022


from dataclasses import dataclass, field
from datetime    import datetime


@dataclass
class User:

    id: int = int()
    username: str = str()
    first_name: str = str()
    last_request: datetime = datetime
    blocked: bool = False
    state: int = int()
    state_for_chat: int = int()
    admin: bool = False
    in_chats: list[int] = field(default_factory=[int])
    pm_started: bool = False
