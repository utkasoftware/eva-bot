"""
Имя файла хендлера не должно начинаться с _, как этот файл.
Динлодер пропускает такие файлы

"""

from telethon.events import (
    register as _reg,
    NewMessage
)

from ..eva import local


@_reg(
    NewMessage(
        incoming=True,
        forwards=False,
        pattern=r"/start")
)
async def ping__cmd(event) -> None:
    """
    '__cmd' обязателен после имени хендлера,
    чтобы динамический загрузчик отработал правильно.
    """
    await event.respond(local.ping_respond)

