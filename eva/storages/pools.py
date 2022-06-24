# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022

from psycopg2 import pool
from eva.configs import BotConfig


class Pool:

    def __init__(this):

        params = BotConfig().get_connect_params()
        this.pool = pool.SimpleConnectionPool(
            1,
            25,
            user=params.user,
            password=params.password,
            database=params.database,
            host=params.host,
            port=params.port
        )

    def get_connection(this):
        return this.pool.getconn()

