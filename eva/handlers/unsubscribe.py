from telethon.events import (
    register as _reg,
    NewMessage
)

from .. import (
    usc,
    bot_manage
)


@_reg(
    NewMessage(
        incoming=True,
        forwards=False,
        pattern=r"/unsubscribe",
        func=lambda e: e.is_private)
)
@bot_manage.limiter()
@usc.START
async def unsubscribe__cmd(event):
    # @todo
    # await user_storage.unsubscribe(user_id=event.sender.id)
    await event.respond("ОК! Вы отказались от рассылки.")

