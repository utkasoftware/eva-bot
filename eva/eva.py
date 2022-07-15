# cython: language_level=3
# -*- coding: utf-8 -*-

import asyncio

from markupsafe import escape

from telethon import events # type: ignore
from telethon.errors.rpcbaseerrors import BadRequestError  # type: ignore
from telethon.tl.custom.message import Message

from telethon.tl.functions.messages import (
    HideChatJoinRequestRequest as HideChatJoinRequestRequest  # type: ignore
)

from telethon.errors.rpcerrorlist import (
    ChannelPrivateError    as ChannelPrivateError,
    ChatAdminRequiredError as ChatAdminRequiredError
)

from . import (
    bot,
    local,
    config,
    usc,
    utils,
    logger,
    bot_manage,
    user_storage,
    chat_storage,
    captcha_storage,
    captcha_wrapper,
    User
)

from . import handlers


captcha_settings = config.get_captcha_settings()



@bot.on(events.NewMessage(incoming=True, forwards=False))
async def all_handler(event: Message) -> None:
    """
    Сбор данных пользователей и хендлер для ответов на капчу
    @todo перенести всё в обработчик заявок под telethon.conversation
    Держать обязательно в самом начале хендлеров.
    """

    if not utils.is_channel(event) and utils.is_private(event):
        await user_storage.save_user(event)

    if utils.is_private(event) and not event.message.text.startswith("/"):

        user_state = await usc.get(event.sender.id)

        if user_state == usc.states.FEEDBACK_WAIT_FOR_ANSWER:
            await feedback_thanks(event)

        if user_state == usc.states.WAIT_FOR_ANSWER:
            await captcha_answer(event)


async def feedback_thanks(event):

    await bot.forward_messages(bot_manage.owner_id, event.message)
    await event.respond(local.feedback_thanks)
    await usc.update(event.chat.id, usc.states.START)


@bot.on(events.CallbackQuery)
async def callback_handler(event):
    """
    Колбэки от инлайн-кнопок
    Форматы bytes-данных:
        '<действие>.<данные>'
        Доступные действия:
            join    | j<chat_id:int>
            connect | c<chat_id:int>.<channel_id:int>
            cancel  | cancel
            ...
        Пример:
            'j1000000'
            'c1000000.1200000'
    """

    decoded_data = event.data.decode("utf-8")
    action = decoded_data
    user_id = int(event.query.user_id)

    if action == "cancel":
        await event.edit(local.cancelled)
        await usc.update(user_id, usc.states.START)
        return

    if action[0] == "j":
        chat_id = decoded_data[1:]
        _captcha = captcha_wrapper.generate(*captcha_settings)

        await captcha_storage.add_captcha(
            user_id=user_id, text=_captcha.text, chat_id=chat_id
        )
        await event.edit(local.enter_image_text)
        await bot.send_message(user_id, file=_captcha.image)
        await usc.update(user_id, usc.states.WAIT_FOR_ANSWER)

    if action[0] == "c":
        chat_id = int(decoded_data[1:].split(".")[0])
        channel_id = int(decoded_data[1:].split(".")[1])
        if chat_id < 0:
            chat_id = -1_000_000_000_000 + chat_id

        user_permissions = await bot.get_permissions(entity=chat_id, user=user_id)
        if not user_permissions.is_admin:
            await event.answer(local.you_dont_have_admin_perms, alert=True)
            return
        try:
            await bot.send_message(
                channel_id, local.log_channel_added_post.format(
                    escape(event.chat.title)
                )
            )
        except ChannelPrivateError:
            await event.edit(local.log_channel_add_error)
            return
        except ChatAdminRequiredError:
            await event.edit(local.log_channel_missing_perms)
            return
        else:
            await event.edit(local.log_channel_added)
            await chat_storage.set_log_channel(chat_id, channel_id)
            return


@bot.on(events.ChatAction)
async def new_add_greetings(event: Message) -> None:

    if event.user_added and bot_manage.bot_id in event.action_message.action.users:
        await bot.send_message(event.chat, local.start_text)
        await asyncio.sleep(1)
        await bot.send_message(
            event.chat,
            local.promote_me_please,
        )

@bot_manage.limiter(only_private=True)
async def captcha_answer(event):
    answer = event.message.text
    if len(answer) > 32:
        await bot.send_message(event.sender.id, local.max_symbols_error)
        return
    for char in answer:
        if char.isalpha() or char.isnumeric():
            continue
        await bot.send_message(event.sender.id, local.incorrect_answer)
        break

    captcha = await captcha_storage.solve_captcha(
        user_id=event.sender.id, text=answer
    )
    if captcha.error:
        await bot.send_message(
            event.sender.id,
            local.captcha_critical_error,
        )
        return
    if captcha.found:
        if captcha.expired:
            new_captcha = captcha_wrapper.generate(*captcha_settings)
            await bot.send_message(
                event.sender.id,
                local.captcha_code_expired,
            )

            await captcha_storage.refresh_captcha(
                id=captcha.id, new_text=new_captcha.text
            )
            await bot.send_file(
                event.sender.id,
                file=new_captcha.image,
                caption=local.captcha_wait_for_answer,
            )
            return
        try:

            log_channel_id = await chat_storage.get_log_channel(captcha.for_chat)
            await bot(
                HideChatJoinRequestRequest(
                    peer=captcha.for_chat,
                    user_id=event.sender.id,
                    approved=True,
                )
            )

            await bot.send_message(
                event.sender.id,
                local.request_approved,
            )
            await usc.update(event.sender.id, usc.states.START)
            if log_channel_id:
                new_approve = "#NEW_APPROVE"
                new_approve += "\n<b>Chat:</b> [#peer{}]".format(
                    captcha.for_chat
                )
                new_approve += "\n<b>User:</b> {} [@{}][#id{}]".format(
                    escape(event.sender.first_name),
                    event.sender.username if event.sender.username else "",
                    event.sender.id,
                )
                try:
                    await bot.send_message(log_channel_id, new_approve)
                except ChannelPrivateError:
                    await chat_storage.set_log_channel(captcha.for_chat, 0)

        except BadRequestError:
            await bot.send_message(
                event.sender.id,
                local.approve_error,
            )
            await usc.update(event.sender.id, usc.states.START)
            return


@bot.on(events.NewMessage(incoming=True, forwards=False, pattern=r"(/)start"))
@bot_manage.limiter(only_private=True)
@usc.START
async def start_cmd(event: Message) -> None:

    await event.respond(local.start_text)
    await utils.log_event(event, "/start")


@bot.on(events.ChatAction(func=lambda e: e.new_join_request))
async def join_requests_handler(event: Message) -> None:
    """
    Главный обработчик новых заявок.

    """

    chat_id = (
        event.chat_id
        if not str(event.chat_id).startswith("-100")
        else int(str(event.chat_id)[4:])
    )

    log_channel_id = await chat_storage.get_log_channel(chat_id)

    captcha = captcha_wrapper.generate(*captcha_settings)
    await user_storage.add_user(
        User(
            id=event.user.id,
            first_name=event.user.first_name
        )
    )
    await captcha_storage.add_captcha(
        user_id=event.user_id, text=captcha.text, chat_id=chat_id
    )

    await bot.send_file(
        event.user_id,
        file=captcha.image,
        caption=local.captcha_greetings.format(escape(event.chat.title)),
    )
    await usc.update(event.user_id, usc.states.WAIT_FOR_ANSWER)
    if log_channel_id:
        new_request = "#NEW_JOINREQUEST"
        new_request += "\n<b>Chat:</b> {} [#peer{}]".format(
            escape(event.chat.title), event.chat.id
        )
        new_request += "\n<b>User:</b> {} [@{}][#id{}]".format(
            escape(event.user.first_name),
            event.user.username if event.user.username else "",
            event.user.id,
        )
        try:
            await bot.send_message(log_channel_id, new_request)
        except ChannelPrivateError:
            """
            Нас кикнули или отобрали права на публикацию сообщений.
            Обнуляем поле с подключенным каналом
            """
            await chat_storage.set_log_channel(event.chat.id, 0)


def register_handlers():

    for handler in handlers.__all__:
        bot.add_event_handler(
            getattr(handlers, handler)
        )
        logger.notice("handler '{}' registered".format(
            handler)
        )


def start(optional_args):

    if optional_args.log_level != logger.DEFAULT_LEVEL:
        logger.setLevel(optional_args.log_level)

    bot_token = config.get_bot_token()

    register_handlers()

    bot.start(bot_token=bot_token)
    bot.parse_mode = "html"

    logger.success("Started for {}".format(bot_manage.bot_id))
    logger.success("Admin ID: {}".format(config.get_owner_id()))

    bot.run_until_disconnected()
