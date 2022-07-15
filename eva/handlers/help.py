"""
Имя файла хендлера не должно начинаться с _, как этот файл.
Динлодер пропускает такие файлы

"""

from telethon.events import (
    register as _reg,
    NewMessage
)
from telethon.tl.custom import Button

from .. import (
    bot_manage,
    local,
    utils
)


@_reg(
    NewMessage(
        incoming=True,
        forwards=False,
        pattern=r"/help")
)
@bot_manage.limiter(anonymous=True)
async def help__cmd(event):
    if utils.is_private(event):
        await event.client.send_file(
            event.chat,
            file=(
                "https://raw.githubusercontent.com/utkasoftware/eva-bot"
                "/master/assets/help_banner.jpg"
            ),
            caption=local.help_text,
            buttons=Button.url(
                local.help_add_to_group,
                "https://t.me/{}?startgroup=start&admin=invite_users".format(
                    bot_manage.bot_username
                )
            )  # button
        )
        return
    await event.reply(
        local.help_go_pm,
        buttons=Button.url(
            local.help_btn_text,
            "https://t.me/{}?start=help".format(bot_manage.bot_username)
        )
    )
    await utils.log_event(event, "/help")

