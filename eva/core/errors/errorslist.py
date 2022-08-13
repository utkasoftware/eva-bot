# -*- coding: utf-8 -*-


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


class InvalidTokenError(Exception):

    def __init__(this, token: str, api_response: str):
        super().__init__(
            (
            "Bot token '{0}' is not valid. "
            "Please check the config file and set the correct token\n"
            "BotAPI response: '{1}'"
            .format(token, api_response)
            )
        )
