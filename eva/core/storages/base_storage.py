# -*- coding: utf-8 -*-

from eva.modules import Singleton
from ..errors import StorageException
from .pools import Pool


class Storage(metaclass=Singleton):

    """
    Базовый класс репозитория.
    Создает единый пул соединения и передает коннекторы this.con дочерним классам.
    Разрешён только один экземпляр (см. метакласс) на весь жизненный цикл модуля.
    """

    def __init__(this):

        try:
            this.__pool = Pool()
            this.con = this.__get_connection()
        except Exception as e:
            raise StorageException(*e.args, **e.kwargs) from e

    def __get_connection(this):
        return this.__pool.get_connection()

    def complete_transaction(this):
        """
        Закрываем транзакцию или откатываем курсор до предыдущего состояния при неудаче
        """
        try:
            this.con.commit()
        except Exception as e:
            this.con.rollback()
            raise StorageException(*e.args) from e
