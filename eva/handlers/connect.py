from markupsafe import escape

from telethon.tl.custom import Button
from telethon.errors.rpcerrorlist import (
    ChannelPrivateError,
    ChatAdminRequiredError,
    ChatIdInvalidError
)
from telethon.events import (
    register as _reg,
    NewMessage
)

from .. import (
    bot_manage,
    local,
    utils,
    logger,
    chat_storage
)


@_reg(
    NewMessage(
        incoming=True,
        forwards=False,
        pattern=r"/connect")
)
@bot_manage.limiter(no_private=True, anonymous=True)
async def connect__cmd(event):
    chat_id = event.chat.id
    admin_rights = event.chat.admin_rights
    
    if not admin_rights:
        await event.respond(local.connect_missing_perms)
        return

    if event.forward and event.forward.is_channel:

        await utils.log_event(event, "connect")

        if utils.is_anon(event):
            await event.respond(
                local.connect_anonymous_detected,
                buttons= [
                    Button.inline(
                        local.connect_confirm_button,
                        bytes(
                            "c${}.{}".format(
                            event.chat.id,
                            event.forward.from_id.channel_id
                            ),
                            encoding="utf-8"
                        )
                    )
                ]
            )
            return
        try:
            user_permissions = await event.client.get_permissions(
                chat_id if chat_id < 0 else -(1_000_000_000_000 + chat_id),
                user=event.sender.id
            )
            if not user_permissions.is_admin:
                await event.reply(local.you_dont_have_admin_perms)
                return
        except ChatIdInvalidError as e:
            logger.error(e)

        try:
            await event.client.send_message(
                event.forward.from_id.channel_id,
                local.log_channel_added_post.format(
                    escape(event.chat.title)
                )
            )
        except ChannelPrivateError:
            await event.respond(local.log_channel_add_error)
            return
        except ChatAdminRequiredError:
            await event.respond(local.log_channel_missing_perms)
            return
        except Exception as e:
            logger.error(e)
        else:
            await event.respond(local.log_channel_added)
            await chat_storage.set_log_channel(
                event.chat.id,
                event.forward.from_id.channel_id
            )
    else:
        await event.respond(local.connect_forward_cmd)

