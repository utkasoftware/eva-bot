from telethon.events import (
    register as _reg,
    NewMessage
)

from .. import (
    usc,
    bot_manage,
    local,
    utils
)

@_reg(NewMessage(
    incoming=True,
    forwards=False,
    pattern=r"/cancel",
    func=lambda e: e.is_private)
)
@usc.ANY_NOT_IDLE
@bot_manage.limiter()
async def cancel__cmd(event) -> None:
    await usc.update(event.sender.id, usc.states.START)
    await event.respond(local.cancelled)
    await utils.log_event(event, "/cancel")
