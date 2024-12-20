# -*- coding: utf-8 -*-


from httpx import AsyncClient, codes, TimeoutException

from eva.core.config import Config
from eva.modules import logger


class SpamwatchWrapper:
    #@todo update me

    def __init__(this, token: str = Config().get_spamwatch_token()):

        this.token = token

    async def check(this, user_id: int):
        """
        returns False if user found in spamwatch's db
        """

        async with AsyncClient(
            headers={"Authorization": "Bearer {}".format(this.token)}, timeout=5
        ) as client:
            try:
                response = await client.get("https://api.spamwat.ch/banlist/{}".format(user_id))
            except TimeoutException as e:
                logger.error(e)
                # слишком долго ждем api, юзер технически проходит
                return True
        if response.status_code != codes.OK:
            # юзера нет в бд
            return True
        return False
