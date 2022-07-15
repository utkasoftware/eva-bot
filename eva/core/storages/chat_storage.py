# -*- coding: utf-8 -*-

from datetime import datetime
from psycopg2 import sql

from . import Storage


class ChatStorage(Storage):

    """
    Репозиторий для работы с данными групп в базе.
    this.con получает от суперкласса.
    """

    NA = "none"  # Значение по умолчанию для полей без данных

    def __init__(this):
        super().__init__()
        this.__create()

    def __create(this):
        cur = this.con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chats_stats
                (chat_id BIGINT PRIMARY KEY NOT NULL,
                domain VARCHAR(64),
                name VARCHAR(64),
                is_mega BOOLEAN,
                is_admin BOOLEAN,
                last_act TIMESTAMP,
                log_channel BIGINT,
                first_add TIMESTAMP,
                stopped BOOLEAN NOT NULL DEFAULT FALSE,
                blocked BOOLEAN NOT NULL DEFAULT FALSE,
                ads BOOLEAN NOT NULL DEFAULT TRUE);
            """
        )
        this.complete_transaction()

    async def save_chat(this, data) -> None:
        """Запись данных группы в базу"""

        chat = data.chat
        cur = this.con.cursor()
        chat_id = chat.id
        title = (
            (chat.title[:62] + "..")
            if len(chat.title) > 62
            else chat.title
        )

        domain = chat.username if chat.username is not None else this.NA
        is_mega = chat.megagroup
        is_admin = bool(chat.admin_rights)

        cur.execute(
            sql.SQL(
                """
                INSERT
                    INTO chats_stats
                        (chat_id, domain, name, is_mega, is_admin)
                    VALUES
                        (%(in_chat_id)s, %(in_domain)s, %(in_name)s, %(in_is_mega)s, %(in_is_admin)s)
                ON CONFLICT
                    (chat_id)
                DO UPDATE
                    SET
                        (domain, name, is_mega, is_admin) = (excluded.domain, excluded.name, excluded.is_mega, excluded.is_admin)
                """
            ),
            {
                "in_chat_id": chat_id,
                "in_name": title,
                "in_domain": domain,
                "in_is_mega": is_mega,
                "in_is_admin": is_admin,
            },
        )
        this.complete_transaction()

    async def set_log_channel(this, chat_id, channel_id) -> None:
        """Подключаем указанный channel_id канала к группе для логгирования"""

        cur = this.con.cursor()
        cur.execute(
            """
            UPDATE
                chats_stats
            SET
                log_channel = %(chid)s
            WHERE
                chat_id = %(cid)s
            """,
            {"chid": channel_id, "cid": chat_id},
        )
        this.complete_transaction()

    async def get_log_channel(this, chat_id) -> int:
        """Получение channel_id логгинг-канала для группы"""

        cur = this.con.cursor()
        cur.execute(
            """
            SELECT
                log_channel
            FROM
                chats_stats
            WHERE
                chat_id = %(cid)s
            """,
            {"cid": chat_id},
        )
        row = cur.fetchone()
        if not row:
            return
        channel_id = row[0]
        return channel_id

    async def get_chat_limits(this, chat_id: int) -> list[str]:
        """Получение локальных ограничений группы.
        last_act: timestamp - время последнего интерактива с ботом.
        """

        cur = this.con.cursor()
        cur.execute(
            """
            SELECT
                last_act, blocked
            FROM
                chats_stats
            WHERE
                chat_id = %(cid)s
        """,
            {"cid": chat_id},
        )
        row = cur.fetchone()
        if not row:
            return []
        return [row[0], row[1]]

    async def update_chat_limits(this, chat_id) -> None:
        """Обновление локальных ограничений группы"""

        cur = this.con.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur.execute(
            """
            UPDATE
                chats_stats
            SET
                last_act = %(t)s
            WHERE
                chat_id = %(cid)s
            """,
            {"t": now, "cid": chat_id},
        )
        this.complete_transaction()

    async def get_chat_members(this, chat_id) -> list[int]:
        """Получение списка с целыми числами user_id участников группы"""

        cur = this.con.cursor()
        cur.execute(
            """
            SELECT
                user_id, name, domain
            FROM
                users_stats
            WHERE
                in_chats @> ARRAY[%(chatid)s]::int[]
        """,
            {"chatid": chat_id},
        )
        rows = cur.fetchall()
        if not rows:
            return []
        _ids = [row[0] for row in rows]
        """
        @todo deprecated

        """
        _names = [_name.strip() for _name in [row[1] for row in rows]]
        _domains = [_domain.strip() for _domain in [row[2] for row in rows]]

        result = []
        for i in range(len(_ids)):
            result.append([_ids[i], _names[i], _domains[i]])
        return result
