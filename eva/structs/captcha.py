# -*- coding: utf-8 -*-


from dataclasses import dataclass


@dataclass
class Captcha:

    id: int = int()
    text: str = str()
    image: object = object()
    width: int = int()
    height: int = int()
    length: int = int()
    found: bool = False
    error: bool = False
    error_msg: str = str()
    expired: bool = False
    accepted: bool = False
    for_chat: int = int()
    created_at: str = str()
