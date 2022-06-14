# cython: language_level=3
# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022

import asyncio

import coloredlogs
logging = coloredlogs.logging

from markupsafe import escape

from telethon import TelegramClient, events  # type: ignore
from telethon.errors.rpcbaseerrors import BadRequestError  # type: ignore
from telethon.tl.custom import Button  # type: ignore
from telethon.tl.custom.message import Message
from telethon.tl.functions.channels import GetChannelsRequest
from telethon.tl.functions.messages import HideChatJoinRequestRequest  # type: ignore
from telethon.tl.functions.messages import GetChatsRequest
from telethon.errors.rpcerrorlist import ChannelPrivateError
from telethon.errors.rpcerrorlist import ChatAdminRequiredError
from telethon.errors.rpcerrorlist import ChatIdInvalidError

from eva import BotSecurity
from eva import UserStatesControl
from eva import Captcha
from eva import CaptchaWrapper
from eva import Language
from eva import utils

Usc = UserStatesControl()
States = Usc.states

BotSecurity = BotSecurity()
BotDB = BotSecurity.DatabaseWrapperExtended
BotConfig = BotDB.BotConfigExtended

# Locale Language
LL = Language.load("ru")

CaptchaWrapper = CaptchaWrapper()

captcha_settings = BotConfig.get_captcha_settings()
api_id, api_hash = BotConfig.get_api_params()

bot = TelegramClient("main", api_id, api_hash, flood_sleep_threshold=30)


@bot.on(events.NewMessage(incoming=True, forwards=False))
async def all_handler(event: Message) -> None:
    """
    Сбор данных пользователей и хендлер для ответов на капчу
    @todo перенести всё в обработчик заявок под telethon.conversation
    Держать обязательно в самом начале хендлеров.
    """

    if not utils.is_channel(event):
        await BotDB.save_user(event)

    if utils.is_private(event) and not event.message.text.startswith("/"):

        user_state = await Usc.get(event.sender.id)

        if user_state == States.FEEDBACK_WAIT_FOR_ANSWER:

            await bot.forward_messages(BotSecurity.owner_id, event.message)
            await event.respond(LL.feedback_thanks)
            await Usc.update(event.chat.id, States.START)
            return

        if user_state == States.WAIT_FOR_ANSWER:

            answer = event.message.text

            if len(answer) > 32:
                await bot.send_message(event.sender.id, LL.max_symbols_error)
                return

            for char in answer:
                if char.isalpha() or char.isnumeric():
                    continue
                else:
                    await bot.send_message(event.sender.id, LL.incorrect_answer)
                    return

            captcha = await BotDB.solve_captcha(
                user_id=event.sender.id, text=answer
            )

            if captcha.found:

                if captcha.expired:

                    new_captcha = CaptchaWrapper.generate(*captcha_settings)
                    await bot.send_message(
                        event.sender.id,
                        LL.captcha_code_expired,
                    )

                    await BotDB.refresh_captcha(id=captcha.id, new_text=new_captcha.text)
                    await bot.send_file(event.sender.id,
                        file=new_captcha.image,
                        caption=LL.captcha_wait_for_answer,
                    )
                    return

                try:

                    log_channel_id = await BotDB.get_log_channel(captcha.for_chat)
                    await bot(
                        HideChatJoinRequestRequest(
                            peer=captcha.for_chat,
                            user_id=event.sender.id,
                            approved=True,
                        )
                    )

                    await bot.send_message(
                        event.sender.id,
                        LL.request_approved,
                    )
                    await Usc.update(event.sender.id, States.START)
                    if log_channel_id:
                        new_approve = "#NEW_APPROVE"
                        new_approve += "\n<b>Чат:</b> [#peer{}]".format(
                            captcha.for_chat
                        )
                        new_approve += "\n<b>Пользователь:</b> {} [@{}][#id{}]".format(
                            escape(event.sender.first_name),
                            event.sender.username if event.sender.username else "",
                            event.sender.id,
                        )
                        await bot.send_message(log_channel_id, new_approve)

                except BadRequestError:
                    await bot.send_message(
                        event.sender.id,
                        LL.approve_error,
                    )
                    await Usc.update(event.sender.id, States.START)
                    return

                return
            if captcha.error:
                await bot.send_message(
                    event.sender.id,
                    LL.captcha_critical_error,
                )
                return
            return


@bot.on(events.CallbackQuery)
async def callback_handler(event):
    """
    Колбэки от инлайн-кнопок
    Форматы bytes-данных:
        '<действие>.<данные>'
        Доступные действия:
            join    | j<chat_id:int>
            connect | c<chat_id:int>.<channel_id:int>
            ...
        Пример:
            'j1000000'
            'c1000000.1200000'
    """

    decoded_data = event.data.decode("utf-8")
    action = decoded_data[0]
    user_id = int(event.query.user_id)
    if action == "j":
        chat_id = decoded_data[1:]
        _captcha = CaptchaWrapper.generate(*captcha_settings)

        await BotDB.add_captcha(user_id=user_id, text=_captcha.text, chat_id=chat_id)
        await event.edit(LL.enter_image_text)
        await bot.send_message(user_id, file=_captcha.image)
        await Usc.update(user_id, States.WAIT_FOR_ANSWER)

    if action == "c":
        chat_id = int(decoded_data[1:].split(".")[0])
        channel_id = int(decoded_data[1:].split(".")[1])
        if chat_id < 0:
            chat_id = int("-100{}".format(chat_id))

        user_permissions = await bot.get_permissions(entity=chat_id, user=user_id)
        if not user_permissions.is_admin:
            await event.answer(LL.you_dont_have_admin_perms, alert=True)
            return
        try:
            await bot.send_message(
                channel_id, LL.log_channel_added_post.format(escape(event.chat.title))
            )
        except ChannelPrivateError:
            await event.edit(LL.log_channel_add_error)
            return
        except ChatAdminRequiredError:
            await event.edit(LL.log_channel_missing_perms)
            return
        else:
            await event.edit(LL.log_channel_added)
            await BotDB.set_log_channel(chat_id, channel_id)
            return


@bot.on(events.ChatAction)
async def new_add_greetings(event: Message) -> None:

    if event.user_added:
        if BotSecurity.bot_id in event.action_message.action.users:
            await bot.send_message(event.chat, LL.start_text)
            await asyncio.sleep(1)
            await bot.send_message(
                event.chat,
                LL.promote_me_please,
            )


@bot.on(events.NewMessage(incoming=True, forwards=False, pattern=r"(/)feedback"))
@BotSecurity.limiter(only_private=True)
@Usc.START
async def feedback_cmd(event: Message) -> None:

    await bot.send_message(event.chat, LL.feedback_text)
    await Usc.update(event.chat.id, States.FEEDBACK_WAIT_FOR_ANSWER)


@bot.on(events.NewMessage(incoming=True, forwards=False, pattern=r"(/)init"))
@BotSecurity.limiter(no_private=True, anonymous=True)
async def eve_init_cmd(event: Message) -> None:

    admin_rights = event.chat.admin_rights
    public_group = (
        event.chat.username
        if hasattr(event.chat, "username") and event.chat.username
        else False
    )

    wait_msg = await bot.send_message(event.chat.id, LL.initializing)
    await asyncio.sleep(1)
    wait_msg = await bot.edit_message(wait_msg, LL.loading_data)
    if public_group:
        await asyncio.sleep(1)
        await bot.delete_messages(event.chat, message_ids=wait_msg)
        await asyncio.sleep(1)
        await bot.send_message(
            event.chat,
            file="https://i.imgur.com/d04WkmW.gif",
            message=LL.public_group_bye,
        )
        await asyncio.sleep(2)
        await bot.delete_dialog(event.chat)
        return
    if not admin_rights:
        await asyncio.sleep(2)
        wait_msg = await bot.edit_message(
            wait_msg,
            LL.private_group_but_permissions.format(escape(event.chat.title)),
        )
        return

    report = "<i>Чат {} был определен как <b>закрытый</b>...</i>   🆗".format(
        event.chat.title
    )

    if not admin_rights.invite_users:
        report += "\n❗Права админа предоставлены, но не хватает нужных полномочий на:"
        report += "\n <i>> Управление приглашениями и ссылками</i>"
        await bot.edit_message(wait_msg, report)
        return

    report += "\n<i>Права админа предоставлены...   </i>🆗"
    await bot.edit_message(wait_msg, report)
    await asyncio.sleep(1)
    await bot.send_message(event.chat, "Готова к работе.")


@bot.on(events.NewMessage(incoming=True, pattern=r"(/)connect"))
@BotSecurity.limiter(no_private=True, anonymous=True)
async def connect_cmd(event: Message) -> None:

    chat_id = event.chat.id

    admin_rights = event.chat.admin_rights
    if not admin_rights:
        await event.respond(LL.connect_missing_perms)
        return

    if event.forward and event.forward.is_channel:

        if utils.is_anon(event):
            button_text = LL.connect_anonymous_detected
            await bot.send_message(
                event.chat.id,
                button_text,
                buttons=[
                    [
                        Button.inline(
                            "Подтвердить",
                            bytes(
                                "c{}.{}".format(
                                    event.chat.id, event.forward.from_id.channel_id
                                ),
                                encoding="utf-8",
                            ),
                        )
                    ]
                ],
            )
            return

        try:
            user_permissions = await bot.get_permissions(
                chat_id if chat_id < 0 else int("-100{}".format(chat_id)),
                user=event.sender.id,
            )
            if not user_permissions.is_admin:
                await event.reply(LL.you_dont_have_admin_perms)
                return
        except ChatIdInvalidError:
            return

        try:
            await bot.send_message(
                event.forward.from_id.channel_id,
                LL.log_channel_added_post.format(escape(event.chat.title)),
            )
        except ChannelPrivateError:
            await event.respond(LL.log_channel_add_error)
            return
        except ChatAdminRequiredError:
            await event.respond(LL.log_channel_missing_perms)
            return
        else:
            await event.respond(LL.log_channel_added)
            await BotDB.set_log_channel(event.chat.id, event.forward.from_id.channel_id)
            return
    else:
        await event.respond(LL.connect_forward_cmd)

    await utils.log_event(event, "connect")


@bot.on(events.NewMessage(incoming=True, forwards=False, pattern=r"(/)start"))
@BotSecurity.limiter(only_private=True)
@Usc.START
async def start_cmd(event: Message) -> None:

    deeplink_args = utils.get_message_args(event.message)
    if deeplink_args and deeplink_args[0] == "help":
        await send_help(event)
        return
    await event.respond(LL.start_text)
    await utils.log_event(event, "/start")


@bot.on(events.NewMessage(incoming=True, forwards=False, pattern=r"(/)(ping)"))
@BotSecurity.limiter()
async def ping_cmd(event: Message) -> None:

    await event.respond(LL.ping_respond)
    await utils.log_event(event, "/ping")


@bot.on(events.NewMessage(incoming=True, forwards=False, pattern=r"(/)cancel"))
@BotSecurity.limiter(only_private=True)
@Usc.ANY_NOT_IDLE
async def cancel_cmd(event: Message) -> None:

    await event.respond(LL.cancelled)
    await Usc.update(event.sender.id, States.START)
    await utils.log_event(event, "/cancel")


# @bot.on(events.NewMessage(incoming=True, forwards=False, pattern="(?i)ева*"))
# @BotSecurity.limiter(no_private=True, anonymous=True)
async def eva_trigger(event: Message) -> None:

    args = utils.get_message_args(event.message)
    if not args:
        return

    stop_list = ["стоп", "stop"]
    start_list = ["старт", "start", "проснись", "работать"]
    user_command = args[0].lower()
    if user_command in stop_list:
        await BotDB.stop_handling(chat_id=event.chat.id)
        await event.respond(LL.requests_handling_stopped)
        return
    if user_command in start_list:
        await BotDB.start_handling(chat_id=event.chat.id)
        await event.respond(LL.requests_handling_started)
        return


@bot.on(events.NewMessage(incoming=True, forwards=False, pattern=r"(/)join"))
@BotSecurity.limiter(only_private=True)
@Usc.START
async def join_cmd(event: Message) -> None:

    pending_chats: list = await BotDB.get_pending_chats(event.sender.id)
    please_wait = await event.respond(LL.loading_requests_list)
    await utils.log_event(event, "/join")
    if not pending_chats:
        await bot.edit_message(please_wait, LL.requests_not_found)
        return

    if len(pending_chats) == 1:
        pending_chat_id = pending_chats[0]
        button = [
            Button.inline(
                LL.join_btn,
                bytes("j{}".format(pending_chat_id), encoding="utf-8"),
            )
        ]
        try:
            chat_info = await bot(GetChannelsRequest(id=[pending_chat_id]))
        except ChannelPrivateError:
            await bot.edit_message(
                please_wait,
                LL.error_im_kicked,
            )
            await BotDB.delete_all_from_chat(chat_id=pending_chat_id)

            return
        chat_title = chat_info.chats[0].title

        await bot.delete_messages(event.chat, message_ids=please_wait)
        await bot.send_message(
            event.sender.id,
            LL.found_request_to.format(escape(chat_title)),
            buttons=button,
        )
        return

    chats_info = []
    for chat in pending_chats:
        try:
            if chat > 1:
                """
                Супергруппы, мегагруппы и каналы не имеют минуса
                перед числовым ИД (положительные),
                в отличие от маленьких базовых групп, где все админы по умолчанию.
                """
                chat_returned = await bot(GetChannelsRequest(id=[chat]))
            else:
                chat_returned = await bot(GetChatsRequest(id=[chat]))
            chats_info.append(chat_returned.chats[0])
        except:
            pass  # FIXME

    buttons = []
    for c in chats_info:

        buttons.append(
            [
                Button.inline(
                    escape(c.title if len(c.title) < 8 else c.title[:8] + ".."),
                    bytes("j{}".format(c.id), encoding="utf-8"),
                )
            ]
        )

    await bot.delete_messages(event.chat, message_ids=please_wait)
    result = LL.found_requests
    await bot.send_message(event.sender.id, result, buttons=buttons)


@bot.on(
    events.NewMessage(incoming=True, forwards=False, pattern=r"(/)(chatid|chat_id)")
)
@BotSecurity.limiter(anonymous=True)
async def chatid_cmd(event: Message) -> None:

    if not utils.is_private(event):
        chatid_text = "<b>{}</b> chat ID: <code>-100{}</code>".format(
            escape(event.chat.title), event.chat.id
        )
        await event.reply(chatid_text)
        await utils.log_event(event, "/chatid")
    else:
        chatid_text = "{} ID <code>{}</code>".format(
            escape(event.sender.first_name), event.chat.id
        )
        await event.reply(chatid_text)
        await utils.log_event(event, "/chatid")


@bot.on(events.NewMessage(incoming=True, forwards=False, pattern=r"(/)help"))
@BotSecurity.limiter(anonymous=True)
async def send_help(event: Message) -> None:

    if utils.is_private(event):

        await bot.send_file(
            event.chat,
            file="https://i.imgur.com/A5loMYy_d.jpg?maxwidth=4096",
            caption=LL.help_text,
        )
        await utils.log_event(event, "/help")
    else:
        await bot.send_message(
            entity=event.chat.id,
            reply_to=event.message.id,
            message=LL.help_go_pm,
            buttons=[
                [
                    Button.url(
                        LL.help_btn_text,
                        "https://t.me/{}?start=help".format(BotSecurity.bot_username),
                    )
                ]
            ],
        )
        await utils.log_event(event, "/help")


@bot.on(events.ChatAction(func=lambda e: e.new_join_request))
async def join_requests_handler(event: Message) -> None:
    """
    Главный обработчик новых заявок.

    """

    _chat_id = (
        event.chat_id
        if not str(event.chat_id).startswith("-100")
        else int(str(event.chat_id)[4:])
    )

    log_channel_id = await BotDB.get_log_channel(_chat_id)

    _captcha = CaptchaWrapper.generate(*captcha_settings)
    await BotDB.add_user(user_id=event.user.id, name=event.user.first_name)
    await BotDB.add_captcha(user_id=event.user_id, text=_captcha.text, chat_id=_chat_id)

    greeting = LL.captcha_greetings

    await bot.send_file(
        event.user_id,
        file=_captcha.image,
        caption=greeting.format(escape(event.chat.title)),
    )
    await Usc.update(event.user_id, States.WAIT_FOR_ANSWER)
    if log_channel_id:
        new_request = "#NEW_JOINREQUEST"
        new_request += "\n<b>Чат:</b> {} [#peer{}]".format(
            escape(event.chat.title), event.chat.id
        )
        new_request += "\n<b>Пользователь:</b> {} [@{}][#id{}]".format(
            escape(event.user.first_name),
            event.user.username if event.user.username else "",
            event.user.id,
        )
        await bot.send_message(log_channel_id, new_request)


@bot.on(events.NewMessage(incoming=True, forwards=False, pattern=r"(/)new"))
@BotSecurity.limiter(only_private=True)
@Usc.WAIT_FOR_ANSWER
async def renew_captcha_cmd(event: Message) -> None:

    _captcha = CaptchaWrapper.generate(*captcha_settings)

    await BotDB.renew_captcha(user_id=event.sender.id, text=_captcha.text)
    await event.respond(LL.captcha_updated, file=_captcha.image)
    await utils.log_event(event, "/new")


def start(optional_args):

    default_format = "%(asctime)s %(funcName)s::%(lineno)d %(levelname)s: %(message)s"
    logger = logging.getLogger(__name__)
    coloredlogs.install(level="INFO", fmt=default_format)

    BotDB.create()
    BOT_TOKEN = BotConfig.get_bot_token()

    bot.start(bot_token=BOT_TOKEN)
    bot.parse_mode = "html"

    logger.info("Started for {}".format(BotSecurity.bot_id))
    logger.info("Admin ID: {}".format(BotConfig.get_owner_id()))

    bot.run_until_disconnected()
