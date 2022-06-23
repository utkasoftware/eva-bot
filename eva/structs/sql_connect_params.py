# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022


from dataclasses import dataclass

@dataclass
class SqlConnectParams:

    database: str
    user: str
    password: str
    host: str
    port: int

