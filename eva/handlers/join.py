from markupsafe import escape

from telethon.tl.custom import Button
from telethon.tl.functions.messages import GetChatsRequest
from telethon.tl.functions.channels import GetChannelsRequest
from telethon.errors.rpcerrorlist import ChannelPrivateError

from telethon.events import (
    register as _reg,
    NewMessage
)

from .. import (
    usc,
    bot_manage,
    local,
    logger,
    captcha_storage
)


@_reg(
    NewMessage(
        incoming=True,
        forwards=False,
        pattern=r"/join",
        func=lambda e: e.is_private)
)
@bot_manage.limiter()
@usc.START
async def join__cmd(event):
    pending_chats = await captcha_storage.get_pending_chats_for(
        event.sender.id
    )

    if not pending_chats:
        await event.respond(local.requests_not_found)
        return

    please_wait = await event.respond(local.loading_requests_list)

    if len(pending_chats) == 1:
        pending_chat_id = pending_chats[0]
        button = [
            Button.inline(
                local.join_btn,
                bytes("j{}".format(pending_chat_id), encoding="utf-8")
            )
        ]
        try:
            pending_chat_info = await event.client(
                GetChannelsRequest(id=[pending_chat_id])
            )
        except ChannelPrivateError:
            await event.client.edit_message(
                please_wait,
                local.error_im_kicked
            )
            await captcha_storage.delete_all_from_chat(chat_id=pending_chat_id)
            return
        chat_title = pending_chat_info.chats[0].title

        await event.client.delete_messages(
            event.chat,
            message_ids=please_wait
        )
        await event.client.send_message(
            event.chat,
            local.found_request_to.format(
                escape(chat_title)
            ),
            buttons=button
        )
        return

    chats_list = []
    for chat_id in pending_chats:
        try:
            if chat_id > 1:
                """
                Супергруппы, мегагруппы и каналы не имеют минуса
                перед числовым ИД (положительные),
                в отличие от маленьких базовых групп, где все админы по умолчанию.
                """
                chat_returned = await event.client(
                    GetChannelsRequest(id=[chat_id])
                )
            else:
                chat_returned = await event.client(
                    GetChatsRequest(id=[chat_id])
                )
            chats_list.append(chat_returned.chats[0])
        except ChannelPrivateError:
            continue  # @todo add skipped count to result msg

        except Exception as e:
            logger.fatal(e)

    buttons = []
    for chat in chats_list:

        buttons.append(
            [
                Button.inline(
                    escape(chat.title
                    if len(chat.title) < 8
                    else chat.title[:8] + ".."),
                    bytes("j{}".format(chat.id), encoding="utf-8"),
                )
            ]
        )

    await event.cliet.delete_messages(
        event.chat,
        message_ids=please_wait
    )
    await event.client.send_message(
        event.sender.id,
        local.found_requests,
        buttons=buttons
    )


