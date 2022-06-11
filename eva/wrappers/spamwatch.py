# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022

from httpx import AsyncClient, codes, TimeoutException

from ..configs import BotConfig


class SW:

    def __init__(this, token: str = BotConfig().get_spamwatch_token()):

        this.token = token

    async def check(this, user_id: int):
        """
        returns False if user found in spamwatch's db
        """

        async with AsyncClient(
                headers={'Authorization':
                         'Bearer ' + this.token}, timeout=5) as c:
            try:
                response = await c.get("https://api.spamwat.ch/banlist/" +
                                       str(user_id))
            except TimeoutException:
                # слишком долго ждем api, юзер технически проходит
                return True
        if response.status_code != codes.OK:
            # юзера нет в бд
            return True
        return False


if __name__ == '__main__':
    import asyncio
    token = input('SW Token: ')
    sw = SW(token)
    loop = asyncio.new_event_loop()
    while True:
        user_id = int(input('User Id: '))
        print(loop.run_until_complete(sw.check(user_id)))
