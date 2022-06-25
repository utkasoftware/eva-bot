# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022

from eva.modules import Singleton
from eva.errors import StorageException
from .pools import Pool


class Storage(metaclass=Singleton):

    def __init__(this):

        try:
            this.__pool = Pool()
            this.con = this.__get_connection()
        except Exception as e:
            raise StorageException(*e.args, **e.kwargs) from e

    def __get_connection(this):
        return this.__pool.get_connection()

    def complete_transaction(this):
        try:
            this.con.commit()
        except Exception as e:
            this.con.rollback()
            raise StorageException(*e.args) from e
