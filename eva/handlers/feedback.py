from telethon.events import (
    register as _reg,
    NewMessage
)
from telethon.tl.custom import Button

from .. import (
    usc,
    bot_manage,
    local
)


@_reg(
    NewMessage(
        incoming=True,
        forwards=False,
        pattern=r"/feedback",
        func=lambda e: e.is_private)
)
@bot_manage.limiter()
@usc.START
async def feedback__cmd(event):
    await event.respond(
        local.feedback_text,
        link_preview=False,
        buttons= [
            Button.inline(
                local.cancel_btn,
                bytes("cancel", encoding="utf-8")
            )
        ]
    )
    await usc.update(event.sender.id, usc.states.FEEDBACK_WAIT_FOR_ANSWER)

