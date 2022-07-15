from telethon.events import (
    register as _reg,
    NewMessage
)

from .. import (
    bot_manage,
    local,
    utils
)

@_reg(NewMessage(
    incoming=True,
    forwards=False,
    pattern=r"/ping")
)
@bot_manage.limiter()
async def ping__cmd(event) -> None:
    await event.respond(local.ping_respond)
    await utils.log_event(event, "/ping")

