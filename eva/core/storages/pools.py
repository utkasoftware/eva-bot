# -*- coding: utf-8 -*-

from psycopg2 import pool, OperationalError

from eva.modules import Singleton, logger
from ..config import Config


class Pool(metaclass=Singleton):

    def __init__(this):

        this.__pool = this.__create_pool()

    def get_connection(this):
        logger.spam("Created pool connection")
        return this.__pool.getconn()

    def __create_pool(this) -> pool:
        __params = Config().get_connect_params()
        try:
            ret_pool = pool.SimpleConnectionPool(
                1,
                25,
                user=__params.user,
                password=__params.password,
                database=__params.database,
                host=__params.host,
                port=__params.port
            )
            logger.success(
                "Pool successfully created in {}:{}".format(
                    __params.host, __params.port)
            )
        except OperationalError as e:
            logger.fatal(e)

        return ret_pool

    def __update_pool(this):
        this.__pool = this.__create_pool()

    def __check_pool(this):
        # @todo
        pass
