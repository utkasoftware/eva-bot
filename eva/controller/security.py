# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022

from typing import Callable
from functools import wraps
from datetime import datetime
from telethon.events import StopPropagation

from ..wrappers import DatabaseWrapper
from ..structs import States
from .. import utils


class BotSecurity:

    def __init__(this) -> None:

        # DatabaseWrapper <- BotConfig
        # BotSecurity <- DatabaseWrapper, BotConfig
        # eva.py <- BotSecurity, DatabaseWrapper, BotConfig
        this.DatabaseWrapperExtended = DatabaseWrapper()
        this.BotConfigExtended = this.DatabaseWrapperExtended.BotConfigExtended

        this.bot_username = this.BotConfigExtended.get_bot_username()
        this.bot_id = this.BotConfigExtended.get_bot_id()
        this.owner_id = this.BotConfigExtended.get_owner_id()

        this.db_wrapper = this.DatabaseWrapperExtended

    def is_admin(this, user_id: int) -> bool:

        return this.db_wrapper.is_user_admin(user_id)

    def is_owner(this, user_id: int) -> bool:

        return this.owner_id == user_id


    """
    Main decorators

    """

    def admins_deprecated(this, event_func: Callable) -> Callable:
        async def wrapper(*events, **kwargs) -> None:
            data = events[0]
            user_id = data.sender.id
            if this.db_wrapper.is_user_admin(user_id):
                await event_func(*events, **kwargs)
                return
            return

        return wrapper

    def admins(this, check_anon: bool = False) -> Callable:
        def pseudo_decor(event_func: Callable):
            @wraps(event_func)
            async def wrapper(*events, **kwargs) -> None:
                data = events[0]
                user_id = data.sender.id
                if check_anon and utils.is_anon(data):
                    await event_func(*events, **kwargs)
                    return
                if this.db_wrapper.is_user_admin(user_id):
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



    def limiter(
        this,
        only_private_groups: bool = False,
        only_private: bool = False,
        no_private: bool = False,
        cmd_disabled: bool = False,
        use_limiter: bool = True,
        anonymous: bool = False,
        cooldown: int = None,
    ) -> Callable:
        """
        # @todo Refactor me please

        """
        def pseudo_decor(event_function: Callable) -> Callable:
            @wraps(event_function)
            async def wrapper(*events, **kwargs):
                """
                todo refactor that if-else hell

                """

                data = events[0]
                nonlocal anonymous # temp fix
                if utils.is_private(data) and anonymous:
                    anonymous = False
                if not utils.is_anon(data) and anonymous:
                    anonymous = False
                """ Ignoring other bots commands """
                if not utils.is_my_cmd(data.message, this.bot_username):
                    return False

                if utils.is_channel(data):
                    # Ignore channels
                    return False

                if utils.is_anon(data) and anonymous:

                    if only_private:
                        return False
                    if only_private_groups and not utils.is_private(
                        data, group=True
                    ):
                        return False

                    chat_id = data.peer_id.channel_id

                elif utils.is_anon(data) and not anonymous:
                    return False
                else:
                    user_id = data.sender.id

                cd = cooldown
                if cmd_disabled:
                    return False

                if all([only_private, no_private]) or all(
                    [only_private, only_private_groups]
                ):
                    raise Exception(
                        'limiter args conflict. \
Please do not use several opposite params (i.e., \
"only_private" and "no_private") at the same time.'
                    )
                if only_private_groups and not utils.is_private(
                    data, group=True
                ):
                    return False
                elif only_private and not utils.is_private(data):
                    return False
                elif no_private and utils.is_private(data):
                    return False

                if not cd:
                    cd = this.db_wrapper.cooldown

                if anonymous:
                    chat_limits: list = this.db_wrapper.get_chat_limits(
                        chat_id
                    )
                else:
                    user_limits: list = this.db_wrapper.get_user_limits(
                        user_id
                    )

                if anonymous:

                    if chat_limits:
                        last_action, blocked = chat_limits
                        now = int(datetime.now().timestamp())

                        if not last_action and not blocked:
                            await event_function(*events, **kwargs)
                            if use_limiter:
                                this.db_wrapper.update_chat_limiter(
                                    chat_id
                                )
                            raise StopPropagation
                        elif (
                            now - int(last_action.timestamp()) > cd
                            and not blocked
                        ):
                            await event_function(*events, **kwargs)
                            if use_limiter:
                                this.db_wrapper.update_chat_limiter(
                                    chat_id
                                )
                            raise StopPropagation
                        else:
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
                            this.db_wrapper.update_chat_limiter(chat_id)
                        raise StopPropagation
                    return

                elif user_limits:

                    last_request, blocked = user_limits
                    now = int(datetime.now().timestamp())

                    if not last_request and not blocked:
                        await event_function(*events, **kwargs)
                        if use_limiter:
                            this.db_wrapper.update_limiter(user_id)
                        raise StopPropagation
                    elif (
                        now - int(last_request.timestamp()) > cd
                        and not blocked
                    ):
                        await event_function(*events, **kwargs)
                        if use_limiter:
                            this.db_wrapper.update_limiter(user_id)
                        raise StopPropagation
                    else:
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
                        this.db_wrapper.update_limiter(user_id)
                    raise StopPropagation
                return

            return wrapper

        return pseudo_decor


class UserStatesControl:

    """
    User state management

    """

    def __init__(this) -> None:

        this.__DWExtended = DatabaseWrapper()
        this.__db_wrapper = this.__DWExtended

        this.states = States

    async def __get_state(this, events) -> int:

        user_id = events[0].sender.id
        user_state: int = await this.__db_wrapper.get_user_state(user_id)
        return user_state

    async def update(this, user_id: int, new_state: States) -> None:

        value = new_state.value
        await this.__db_wrapper.set_user_state(user_id, state_id=value)

    async def get(this, user_id: int) -> int:

        user_state: int = await this.__db_wrapper.get_user_state(user_id)
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
