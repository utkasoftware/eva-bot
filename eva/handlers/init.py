from markupsafe import escape

from telethon.events import (
    register as _reg,
    NewMessage
)

from .. import (
    bot_manage,
    local,
)


@_reg(NewMessage(
    incoming=True,
    forwards=False,
    pattern=r"/init")
)
@bot_manage.limiter(no_private=True, anonymous=True)
async def init__cmd(event):
    admin_rights = event.chat.admin_rights
    public_group = (event.chat.username if hasattr(event.chat, "username")
                    and event.chat.username else False)
    if public_group:
        chat_type = local.chat_type_public
    else:
        chat_type = local.chat_type_private

    join_request_mode = (event.chat.join_request
                         if hasattr(event.chat, "join_request")
                         and event.chat.join_request else False)
    # wait_msg = await event.respond(local.initializing)

    if public_group and not join_request_mode:
        await event.respond(
            local.public_or_nonrequest_group_bye,
            file=("https://raw.githubusercontent.com/utkasoftware/eva-bot"
                  "/master/assets/error.gif"))
        await event.client.delete_dialog(event.chat)
        return

    if not admin_rights:
        await event.respond(
            local.normal_group_but_permissions.format(escape(event.chat.title),
                                                      chat_type))
        return

    report = local.init_report.format(event.chat.title, chat_type)

    if not admin_rights.invite_users:
        report += local.init_report_not_enough_rights
        await event.respond(report)
        return

    report += local.init_report_success
    await event.respond(report)
    await event.respond(local.ready)
