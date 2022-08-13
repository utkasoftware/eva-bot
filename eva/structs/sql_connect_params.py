# -*- coding: utf-8 -*-


from dataclasses import dataclass


@dataclass
class SqlConnectParams:

    database: str
    user: str
    password: str
    host: str
    port: int
