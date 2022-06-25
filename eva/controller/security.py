# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022

from typing import Callable
from functools import wraps
from datetime import datetime
from telethon.events import StopPropagation

from eva.configs import BotConfig
from eva.structs import States
from eva.storages import UserStorage
from eva.storages import ChatStorage
from eva import utils


class BotSecurity:
    def __init__(this) -> None:

        this.user_storage = UserStorage()
        this.chat_storage = ChatStorage()
        this.bot_config = BotConfig()

        this.bot_username = this.bot_config.get_bot_username()
        this.bot_id = this.bot_config.get_bot_id()
        this.owner_id = this.bot_config.get_owner_id()

    def is_admin(this, user_id: int) -> bool:
        """! Bot admin, not chat or channel"""
        return this.user_storage.is_admin(user_id)

    def is_owner(this, user_id: int) -> bool:
        return this.owner_id == user_id

    """
    Main decorators

    """

    def admins(this, check_anon: bool = False) -> Callable:
        def pseudo_decor(event_func: Callable):
            @wraps(event_func)
            async def wrapper(*events, **kwargs) -> None:
                data = events[0]
                user_id = data.sender.id
                if check_anon and utils.is_anon(data):
                    await event_func(*events, **kwargs)
                    return
                if this.user_storage.is_admin(user_id):
                    await event_func(*events, **kwargs)
                    return
                return
            return wrapper
        return pseudo_decor

    def owner(this, event_func: Callable) -> Callable:
        async def wrapper(*events, **kwargs) -> None:
            data = events[0]
            user_id = data.sender.id
            if user_id == this.owner_id:
                await event_func(*events, **kwargs)
                return
            return

        return wrapper

    def limiter(this, *args, **kwargs) -> Callable:

        only_private_groups = kwargs.get("only_private_groups", False)
        only_private = kwargs.get("only_private", False)
        no_private = kwargs.get("no_private", False)
        use_limiter = kwargs.get("use_limiter", True)
        anonymous = kwargs.get("anonymous", False)
        cooldown = kwargs.get("cooldown", None)

        def pseudo_decor(event_function: Callable) -> Callable:
            @wraps(event_function)
            async def wrapper(*events, **kwargs):
                """
                todo refactor that if-else hell

                """
                data = events[0]
                nonlocal anonymous  # temp fix

                """ Ignoring other bots commands and channel posts """
                if not utils.is_my_cmd(
                    data.message, this.bot_username
                ) or utils.is_channel(data):
                    return False

                if all([utils.is_private(data), anonymous]) or all(
                    [not utils.is_anon(data), anonymous]
                ):
                    anonymous = False

                if all([utils.is_anon(data), anonymous]):
                    if only_private or (
                        only_private_groups and not utils.is_private(data, group=True)
                    ):
                        return False
                    chat_id = data.peer_id.channel_id

                elif utils.is_anon(data) and not anonymous:
                    return False
                else:
                    user_id = data.sender.id

                if all([only_private, no_private]) or all(
                    [only_private, only_private_groups]
                ):
                    raise Exception(
                        'limiter args conflict. \
Please do not use several opposite params (i.e., \
"only_private" and "no_private") at the same time.'
                    )
                if only_private_groups and not utils.is_private(data, group=True):
                    return False
                if only_private and not utils.is_private(data):
                    return False
                if no_private and utils.is_private(data):
                    return False

                cd = cooldown
                if not cd:
                    cd = int(this.bot_config.get_limits("cd"))

                if anonymous:
                    chat_limits: list = await this.chat_storage.get_chat_limits(chat_id)
                else:
                    user_limits: list = await this.user_storage.get_user_limits(user_id)

                if anonymous:

                    if chat_limits:
                        last_action, blocked = chat_limits
                        now = int(datetime.now().timestamp())

                        if not last_action and not blocked:
                            await event_function(*events, **kwargs)
                            if use_limiter:
                                await this.chat_storage.update_chat_limiter(chat_id)
                            raise StopPropagation
                        if now - int(last_action.timestamp()) > cd and not blocked:
                            await event_function(*events, **kwargs)
                            if use_limiter:
                                await this.chat_storage.update_chat_limits(chat_id)
                            raise StopPropagation
                        print(
                            "** id{} has ignored:: \
anonymous admin is banned cooldown has not expired".format(
                                chat_id
                            )
                        )
                        return False
                    else:
                        await event_function(*events, **kwargs)
                        if use_limiter:
                            await this.chat_storage.update_chat_limits(chat_id)
                        raise StopPropagation
                    return

                if user_limits:

                    last_request, blocked = user_limits
                    now = int(datetime.now().timestamp())

                    if not last_request and not blocked:
                        await event_function(*events, **kwargs)
                        if use_limiter:
                            await this.user_storage.update_limits(user_id)
                        raise StopPropagation
                    if now - int(last_request.timestamp()) > cd and not blocked:
                        await event_function(*events, **kwargs)
                        if use_limiter:
                            await this.user_storage.update_limits(user_id)
                        raise StopPropagation
                    print(
                        "** id{} has ignored:: \
user is blocked or cooldown has not expired".format(
                            user_id
                        )
                    )
                    return False

                else:
                    await event_function(*events, **kwargs)
                    if use_limiter:
                        await this.user_storage.update_limits(user_id)
                    raise StopPropagation

            return wrapper
        return pseudo_decor


class UserStatesControl:

    """
    User state management

    """

    def __init__(this) -> None:

        this.user_storage = UserStorage()
        this.states = States

    async def __get_state(this, events) -> int:

        user_id = events[0].sender.id
        user_state: int = await this.user_storage.get_user_state(user_id)
        return user_state

    async def update(this, user_id: int, new_state: States) -> None:

        value = new_state.value
        await this.user_storage.set_user_state(user_id, state_id=value)

    async def get(this, user_id: int) -> int:

        user_state: int = await this.user_storage.get_user_state(user_id)
        return user_state

    def ANY_NOT_IDLE(this, event_func: Callable) -> Callable:
        async def wrapper(*events, **kwargs) -> None:

            user_state: int = await this.__get_state(events)
            if user_state != this.states.START.value:
                await event_func(*events, **kwargs)
            return

        return wrapper

    def START(this, event_func: Callable) -> Callable:
        async def wrapper(*events, **kwargs) -> None:

            user_state: int = await this.__get_state(events)
            if user_state == this.states.START.value:
                await event_func(*events, **kwargs)
            return

        return wrapper

    def WAIT_FOR_ANSWER(this, event_func: Callable) -> Callable:
        async def wrapper(*events, **kwargs) -> None:

            user_state: int = await this.__get_state(events)
            if user_state == this.states.WAIT_FOR_ANSWER.value:
                await event_func(*events, **kwargs)
            return

        return wrapper

    def FEEDBACK_WAIT_FOR_ANSWER(this, event_func: Callable) -> Callable:
        async def wrapper(*events, **kwargs) -> None:

            user_state: int = await this.__get_state(events)
            if user_state == this.states.FEEDBACK_WAIT_FOR_ANSWER.value:
                await event_func(*events, **kwargs)
            return

        return wrapper

    def SELECT_CHAT(this, event_func: Callable) -> Callable:
        async def wrapper(*events, **kwargs) -> None:

            user_state: int = await this.__get_state(events)
            if user_state == this.states.SELECT_CHAT.value:
                await event_func(*events, **kwargs)
            return

        return wrapper

    def GROUP_WAIT_FOR_CMD(this, event_func: Callable) -> Callable:
        async def wrapper(*events, **kwargs) -> None:

            user_state: int = await this.__get_state(events)
            if user_state == this.states.GROUP_WAIT_FOR_CMD.value:
                await event_func(*events, **kwargs)
            return

        return wrapper
