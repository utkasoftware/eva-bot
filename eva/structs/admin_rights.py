# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022

from enum import IntEnum


class AdmRights(IntEnum):

    CHANGE_INFO = 0
    POST_MESSAGES = 1
    EDIT_MESSAGES = 2
    DELETE_MESSAGES = 3
    BAN_USERS = 4
    INVITE_USERS = 5
    PIN_MESSAGES = 6
    ADD_ADMINS = 7
    ANONYMOUS = 8
    MANAGE_CALL = 9
    OTHER = 10
    ANY = 42
