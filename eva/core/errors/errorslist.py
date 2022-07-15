# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022


class StorageException(Exception):

    def __init__(this, message, *errors):
        Exception.__init__(this, message)
        this.errors = errors


class ConfigMissingError(Exception):

    def __init__(this, message: str = str()):

        this.message = message
        if not this.message:
            this.message = "Something went wrong with the config file"

        super().__init__(this.message)


class LimiterArgsConflict(Exception):

    def __init__(this, message: str):

        this.message = message
        super().__init__(this.message)
