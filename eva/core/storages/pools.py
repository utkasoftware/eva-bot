# -*- coding: utf-8 -*-

from psycopg2 import pool, OperationalError
from ..config import Config
from eva.modules import Singleton, logger


class Pool(metaclass=Singleton):

    def __init__(this):

        params = Config().get_connect_params()
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
            logger.success(
                "Pool successfully created in {}:{}".format(
                    params.host, params.port)
            )
        except OperationalError as e:
            logger.fatal(e)
            raise SystemExit

    def get_connection(this):
        logger.spam("Created pool connection")
        return this.pool.getconn()
