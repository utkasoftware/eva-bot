from telethon.events import (
    register as _reg,
    NewMessage
)

from .. import (
    usc,
    bot_manage,
    local,
    utils,
    captcha_storage,
    captcha_wrapper
)


@_reg(
    NewMessage(
        incoming=True,
        forwards=False,
        pattern=r"/new",
        func=lambda e: e.is_private)
)
@bot_manage.limiter()
@usc.WAIT_FOR_ANSWER
async def new__cmd(event):
    captcha = captcha_wrapper.generate()

    await captcha_storage.renew_captcha(
        user_id=event.sender.id,
        text=captcha.text
    )
    await event.respond(
        local.captcha_updated,
        file=captcha.image
    )
    await utils.log_event(event, "/new")

