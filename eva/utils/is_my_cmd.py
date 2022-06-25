# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022


from . import Message


def is_my_cmd(message: Message, my_username: str) -> bool:
    """
    Checking a command for belonging to a specific bot.
    I.e, if bots username 'mybot', then command '/ping@Samplebot' will be ignored,
    but not a '/ping' or '/ping@mybot'
    """

    msg = message.text
    if (
        len(msg.split(" ")[0].split("@")) > 1
        and msg.split(" ")[0].split("@")[1].lower() != my_username.lower()
    ):
        return False
    return True
