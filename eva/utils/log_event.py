# -*- coding: utf-8 -*-


from logging import info
from . import is_private
from . import is_anon
from . import Message


async def log_event(data: Message, cmd: str) -> None:

    # @todo Refactor me
    if is_private(data, group=False):  # type: ignore
        if hasattr(data.sender, "username"):
            info(
                "{} (id{}, {}) -> {} in pm".format(
                    data.sender.first_name,
                    data.sender.id,
                    data.sender.username,
                    cmd,
                )
            )
        else:
            info(
                "{} (id{}) -> {} in pm".format(
                    data.sender.first_name, data.sender.id, cmd
                )
            )
    else:
        if is_anon(data):
            info(
                "AnonAdmin::chat (id{}, {}, {}) -> {}".format(
                    data.chat.id,
                    data.chat.title,
                    data.chat.username,
                    cmd,
                )
            )
            return
        if hasattr(data.chat, "username"):
            info(
                "{} (id{}) -> {} in {} (id{}, {})".format(
                    data.sender.first_name,
                    data.sender.id,
                    cmd,
                    data.chat.title,
                    data.chat.id,
                    data.chat.username,
                )
            )
        else:
            info(
                "{} (id{}) -> {} in {} (id{})".format(
                    data.sender.first_name,
                    data.sender.id,
                    cmd,
                    data.chat.title,
                    data.chat.id,
                )
            )
