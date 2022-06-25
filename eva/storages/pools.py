# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022

from psycopg2 import pool, OperationalError
from eva.configs import BotConfig
from eva.modules import Singleton, logger


class Pool(metaclass=Singleton):

    def __init__(this):

        params = BotConfig().get_connect_params()
        try:
            this.pool = pool.SimpleConnectionPool(
                1,
                25,
                user=params.user,
                password=params.password,
                database=params.database,
                host=params.host,
                port=params.port
            )
        except OperationalError as e:
            logger.fatal(e)
            raise SystemExit

    def get_connection(this):
        return this.pool.getconn()

