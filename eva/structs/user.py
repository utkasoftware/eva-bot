# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022

from typing      import Type
from dataclasses import dataclass, field
from datetime    import datetime


@dataclass
class User:

    id: int = int()
    username: str = str()
    first_name: str = str()
    last_request: Type[datetime] = datetime
    state: int = int()
    state_for_chat: int = int()
    blocked: bool = False
    admin: bool = False
    in_chats: list[int] = field(default_factory=lambda: [int])
    pm_started: bool = False
