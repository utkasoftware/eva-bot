import asyncio

from telethon.errors.rpcerrorlist import FloodWaitError
from telethon.events import (
    register as _reg,
    NewMessage
)

from .. import (
    bot_manage,
    user_storage,
    utils,
    logger
)


@_reg(NewMessage(
    incoming=True,
    forwards=False,
    pattern=r"/massmail")
)
@bot_manage.owner
async def massmail__cmd(event):

    if mail_text := utils.get_message_args(event.message):
        mail_text = " ".join(mail_text)
        mail_text += "\n\n<i>/unsubscribe - отказаться от рассылки.</i>"
    else:
        await event.respond("Empty args")
        return
    WAIT_SEC = 1.5
    users = user_storage.get_all_ids()
    wait_please_msg = await event.respond(
        "Got {} users. It will take a long time (~{}min.), please wait".format(
            len(users), (len(users) * WAIT_SEC) / 60))
    success = errors = floodwaits = 0
    for user in users:
        logger.notice("Sending to.. {}".format(user))
        try:
            await event.client.bot.send_message(user, mail_text)
        except FloodWaitError as fwe:
            floodwaits += 1
            errors += 1
            logger.error("Got FloodWaitError, sleeping {}s".format(
                fwe.seconds)
            )
            if floodwaits > 0 and floodwaits % 2 == 0:
                WAIT_SEC *= 1.2
            asyncio.sleep(fwe.seconds)
        except Exception as e:
            errors += 1
            logger.error("Error: {}".format(e))
        else:
            success += 1
            logger.notice("OK")
        finally:
            await asyncio.sleep(WAIT_SEC)

    await event.client.edit_message(
        wait_please_msg, "Done.\nOK: {}\nErrors: {}".format(success, errors)
        )

