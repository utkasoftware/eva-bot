from markupsafe import escape

from telethon.events import (
    register as _reg,
    NewMessage
)

from .. import (
    bot_manage,
    utils
)


@_reg(NewMessage(
    incoming=True,
    forwards=False,
    pattern=r"/(chatid|chat_id|id)")
)
@bot_manage.limiter(anonymous=True)
async def chatid__cmd(event) -> None:
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
