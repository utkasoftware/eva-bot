# -*- coding: utf-8 -*-

from datetime import datetime
from psycopg2 import sql

from eva.structs import User
from . import Storage


class UserStorage(Storage):

    """
    Репозиторий для работы с данными пользователя в базе.
    this.con получает от суперкласса.
    """

    NA = "none"  # Значение по умолчанию для полей без данных

    def __init__(this):
        super().__init__()
        this.__create()

    def __create(this) -> None:

        cur = this.con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users_stats
                (user_id BIGINT PRIMARY KEY NOT NULL,
                domain VARCHAR(64),
                name VARCHAR(64),
                last_req TIMESTAMP,
                state INT NOT NULL DEFAULT 0,
                state_for_chat BIGINT,
                blocked BOOLEAN NOT NULL DEFAULT FALSE,
                admin BOOLEAN NOT NULL DEFAULT FALSE,
                in_chats int [] NOT NULL DEFAULT array[]::int[],
                pm_started BOOLEAN NOT NULL DEFAULT FALSE);
            """
        )
        this.complete_transaction()

    async def add_user(this, user: User) -> None:
        """
        Добавление пользователя в таблицу с базовыми данными.
        Нужно для случаев когда бот увидел пользователя, но диалога с ним еще не имеет.
        """

        cur = this.con.cursor()
        name = (user.first_name[:62] + "..") \
            if len(user.first_name) > 62 else user.first_name
        cur.execute(
            sql.SQL(
                """
            INSERT
                INTO users_stats
                    (user_id, name)
            VALUES
                (%(in_userid)s, %(in_name)s)
            ON CONFLICT
                (user_id)
            DO UPDATE
                SET
                    name = excluded.name
                    """
            ),
            {"in_userid": user.id, "in_name": name},
        )
        this.complete_transaction()

    async def save(this, data) -> None:
        """
        Запись пользователя в базу. В отличие от add_user,
        этот метод вызывается при каждом update event и перезаписывает обновленные данные, если необходимо.
        """

        cur = this.con.cursor()
        user_id = data.sender.id
        name = (
            (data.sender.first_name[:62] + "..")
            if len(data.sender.first_name) > 62
            else data.sender.first_name
        )

        domain = data.sender.username if data.sender.username is not None else "none"
        if user_id == data.chat.id:
            cur.execute(
                sql.SQL(
                    """
                INSERT
                    INTO users_stats
                        (user_id, domain, name, pm_started)
                    VALUES
                        (%(in_userid)s, %(in_domain)s, %(in_name)s, 'true')
                ON CONFLICT
                    (user_id)
                DO UPDATE
                    SET
                        (name, domain, pm_started) = (excluded.name, excluded.domain, excluded.pm_started)
                        """
                ),
                {"in_userid": user_id, "in_domain": domain, "in_name": name},
            )
        else:
            chat_id = data.chat.id
            chat_title = (
                (data.chat.title[:30] + "..")
                if len(data.chat.title) > 30
                else data.chat.title
            )

            if hasattr(data.chat, "username"):
                chat_domain = (
                    data.chat.username if data.chat.username else this.NA
                )
            else:
                chat_domain = this.NA

            # if chat_mega := hasattr(data.chat, "megagroup"):
            #    pass

            if hasattr(data.chat, "megagroup"):
                chat_mega = data.chat.megagroup
            else:
                chat_mega = False

            cur.execute(
                sql.SQL(
                    """
                INSERT
                    INTO users_stats
                        (user_id, domain, name, in_chats)
                    VALUES
                        (%(in_userid)s, %(in_domain)s, %(in_name)s, ARRAY[ %(chat_arr)s ])
                ON CONFLICT
                    (user_id)
                DO UPDATE
                    SET
                        name = excluded.name,
                        domain = excluded.domain,
                        in_chats = CASE WHEN
                            NOT (users_stats.in_chats @> ARRAY[ %(chat_arr)s ]::int[])
                            THEN users_stats.in_chats || ARRAY[ %(chat_arr)s ]::int[]
                            ELSE users_stats.in_chats end;


                INSERT
                    INTO chats_stats
                        (chat_id, domain, name, is_mega)
                    VALUES
                        (%(in_chatid)s, %(in_cdomain)s, %(in_cname)s, %(in_ismega)s)
                ON CONFLICT
                    (chat_id)
                DO UPDATE
                    SET
                        name = excluded.name,
                        domain = excluded.domain,
                        last_act = now()::timestamp;

            """
                ),
                {
                    "in_userid": user_id,
                    "in_domain": domain,
                    "in_name": name,
                    "chat_arr": data.chat.id,
                    "in_chatid": chat_id,
                    "in_cdomain": chat_domain,
                    "in_cname": chat_title,
                    "in_ismega": chat_mega,
                },
            )
        this.complete_transaction()

    async def get_user(this, user_id: int) -> User | list:
        """Возвращает пользователя в виде экземпляра User или пустой лист"""

        cur = this.con.cursor()
        cur.execute(
            """
            SELECT
                *
            FROM
                users_stats
            WHERE
                user_id = %(id)s
            """,
            {"id": user_id},
        )
        row = cur.fetchone()
        if not row:
            return []
        row = list(row)
        return User(*row)

    async def get_users_count(this) -> int:

        cur = this.con.cursor()
        cur.execute("""SELECT COUNT(DISTINCT user_id) FROM users_stats""")
        count = cur.fetchone()[0]  # tuple
        return count

    async def get_all_ids(this) -> list[int]:

        cur = this.con.cursor()
        cur.execute(
            """SELECT user_id FROM users_stats""")
        rows = cur.fetchall()
        users = [user[0] for user in rows]
        return users

    def get_all_states(this) -> list[list[int, int]]:

        cur = this.con.cursor()
        cur.execute(
            """SELECT user_id, state FROM users_stats""")
        rows = cur.fetchall()
        states = [list(state) for state in rows]
        return states

    async def set_user_state(this, user_id: int, state_id: int) -> None:
        """Устанавливаем состояние пользователя."""

        cur = this.con.cursor()
        cur.execute(
            """
            UPDATE
                users_stats
            SET
                state = %(nstate)s
            WHERE
                user_id = %(uid)s
            """,
            {"nstate": state_id, "uid": user_id},
        )
        this.complete_transaction()

    async def get_user_state(this, user_id: int) -> int:
        """Возвращает состояние пользователя"""

        cur = this.con.cursor()
        cur.execute(
            """
            SELECT
                state
            FROM
                users_stats
            WHERE
                user_id = %(uid)s
            """,
            {"uid": user_id},
        )

        row = cur.fetchone()
        if not row:
            return 0
        state_id = row[0]
        return state_id

    async def get_user_chats(this, user_id: int) -> list[int]:
        """
        Возвращает список с целыми числами - идентификаторами чатов,
        в которых состоит пользователь.
        """

        cur = this.con.cursor()
        cur.execute(
            """
            SELECT
                in_chats
            FROM
                users_stats
            WHERE
                user_id = %(id)s
        """,
            {"id": user_id},
        )
        row = cur.fetchone()
        if not row:
            return []
        if len(row[0]) == 0:
            return []
        return row[0]

    async def ban_user(this, user_id: int) -> None:
        """Локальный бан пользователя"""

        cur = this.con.cursor()
        cur.execute(
            """
            UPDATE
                users_stats
            set
                blocked = 'yes'
            WHERE
                user_id = %(id)s
            """,
            {"id": user_id},
        )
        this.complete_transaction()

    async def unban_user(this, user_id: int) -> None:
        """Локальный разбан пользователя"""

        cur = this.con.cursor()
        cur.execute(
            """
            UPDATE
                users_stats
            set
                blocked = 'no'
            WHERE
                user_id = %(id)s
            """,
            {"id": user_id},
        )
        this.complete_transaction()

    async def is_user_banned(this, user_id: int) -> bool:
        """Проверка пользователя на локальный бан"""

        cur = this.con.cursor()
        cur.execute(
            """
            SELECT
                blocked
            FROM
                users_stats
            WHERE
                user_id = %(id)s
            """,
            {"id": user_id},
        )
        row = cur.fetchone()
        row = list(row)
        return row[0]

    async def set_admin(this, user_id: int, val: str) -> None:
        """Изменение локальных прав пользователя"""

        cur = this.con.cursor()
        cur.execute(
            """
            UPDATE
                users_stats
            SET
                admin = %(new_value)s
            WHERE
                user_id = %(id)s
        """,
            {"new_value": val, "id": user_id},
        )
        this.complete_transaction()

    async def is_admin(this, user_id: int) -> bool:
        """Проверка локальных прав пользователя"""

        cur = this.con.cursor()
        cur.execute(
            """
            SELECT
                admin
            FROM
                users_stats
            WHERE
                user_id = %(id)s
        """,
            {"id": user_id},
        )
        row = cur.fetchone()
        return bool(row[0])

    async def get_user_limits(this, user_id: int) -> list[str]:
        """
        Получение локальных ограничений пользователя.
        last_req: timestamp - время последнего обращения пользователя к боту.
        """

        cur = this.con.cursor()
        cur.execute(
            """
            SELECT
                last_req, blocked
            FROM
                users_stats
            WHERE
                user_id = %(userid)s
        """,
            {"userid": user_id},
        )
        row = cur.fetchone()
        if not row:
            return []
        return [row[0], row[1]]

    async def update_limits(this, user_id: int) -> None:
        """Обновление локальных ограничений пользователя"""

        cur = this.con.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            """
            UPDATE
                users_stats
            SET
                last_req = %(t)s
            WHERE
                user_id = %(id)s
            """,
            {"t": now, "id": user_id},
        )
        this.complete_transaction()
