# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022

from .pools import Pool
from .singleton import Singleton

pool = Pool()

class StorageException(Exception):

    def __init__(this, message, *errors):
        Exception.__init__(this, message)
        this.errors = errors


class Storage(metaclass=Singleton):

    def __init__(this):

        try:
            this.con = this.__get_connection()
        except Exception as e:
            raise StorageException(*e.args, **e.kwargs)

    def __get_connection(this):
        return pool.get_connection()

    def complete_transaction(this):
        try:
            this.con.commit()
        except Exception as e:
            this.con.rollback()
            raise StorageException(*e.args)

