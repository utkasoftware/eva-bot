# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022

from typing import NoReturn, Union
from datetime import datetime
from psycopg2 import sql, connect


from ..structs import Captcha
from ..structs import Message
from ..configs import BotConfig
from ..utils import is_anon


class DatabaseWrapper:

    def __init__(this) -> None:

        # Will import this in eva.py
        this.BotConfigExtended = BotConfig()
        _params = this.BotConfigExtended.get_connect_params()
        # I know about *_params, but it raises
        # "connect() takes from 0 to 3 positional arguments but 5 were given" eror 0_o
        this.con = connect(
            database=_params[0],
            user=_params[1],
            password=_params[2],
            host=_params[3],
            port=_params[4],
        )
        del _params
        this.cooldown: int = int(this.BotConfigExtended.get_limits("cd"))
        this.captcha_timer: int = int(
            this.BotConfigExtended.get_limits("captcha_timer")
        )

    def create(this) -> None:
        cur = this.con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users_stats
                (user_id BIGINT PRIMARY KEY NOT NULL,
                domain CHAR(64),
                name CHAR(64),
                last_req TIMESTAMP,
                state INT NOT NULL DEFAULT 0,
                state_for_chat BIGINT,
                blocked BOOLEAN NOT NULL DEFAULT FALSE,
                admin BOOLEAN NOT NULL DEFAULT FALSE,
                in_chats int [] NOT NULL DEFAULT array[]::int[],
                pm_started BOOLEAN NOT NULL DEFAULT FALSE);
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chats_stats
                (chat_id BIGINT PRIMARY KEY NOT NULL,
                domain CHAR(64),
                name CHAR(64),
                is_mega BOOLEAN,
                last_act TIMESTAMP,
                log_channel BIGINT,
                first_add TIMESTAMP,
                stopped BOOLEAN NOT NULL DEFAULT FALSE,
                blocked BOOLEAN NOT NULL DEFAULT FALSE,
                ads BOOLEAN NOT NULL DEFAULT TRUE);
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS captcha
                (id SERIAL,
                user_id BIGINT,
                ca_approved BOOLEAN NOT NULL DEFAULT FALSE,
                ca_for BIGINT,
                ca_text TEXT,
                ca_time TIMESTAMP);
            """
        )

        this.con.commit()

    async def add_user(this, user_id: int, name: str) -> None:

        """
        Функция для записи юзера с базовыми данными

        """
        cur = this.con.cursor()
        name = (name[:62] + "..") if len(name) > 62 else name

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
            {"in_userid": user_id, "in_name": name},
        )
        this.con.commit()

    async def save_chat(this, data: Message) -> None:

        cur = this.con.cursor()
        chat_id = data.chat.id
        title = (
            (data.chat.title[:62] + "..")
            if len(data.chat.title) > 62
            else data.chat.title
        )

        domain = (
            data.chat.username
            if data.chat.username is not None
            else "none"
        )
        is_mega = data.chat.megagroup
        is_admin = bool(data.chat.admin_rights)

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
                """), {
                    "in_chat_id": chat_id,
                    "in_name": title,
                    "in_domain": domain,
                    "in_is_mega": is_mega,
                    "in_is_admin": is_admin
                }
            )

        this.con.commit()

    async def save_user(this, data: Message) -> None:
        """
        Main function for tracking users.
        It also saves the group ID where the event get, if it is not a PM (block "else")
        """

        if is_anon(data):
            await this.save_chat(data)
            return

        cur = this.con.cursor()
        user_id = data.sender.id
        name = (
            (data.sender.first_name[:62] + "..")
            if len(data.sender.first_name) > 62
            else data.sender.first_name
        )

        domain = (
            data.sender.username
            if data.sender.username is not None
            else "none"
        )
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
                    data.chat.username
                    if data.chat.username is not None
                    else "none"
                )
            else:
                chat_domain = "none"

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

        this.con.commit()

        # FIXME please
        logged_ = " {} (id{}, {}) saved. ".format(name, user_id, domain)
        if data.message.text is not None:
            logged_ += ":-> {}".format(data.message.text[:16])
        if data.chat.id != data.sender.id:
            logged_ = "chatid::{}".format(data.chat.id) + logged_
        print(logged_)

    async def set_log_channel(this, chat_id: int, channel_id: int) -> None:

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

        this.con.commit()

    async def get_log_channel(this, chat_id: int) -> int | None:

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

    async def set_user_state(this, user_id: int, state_id: int) -> None:

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

        this.con.commit()

    async def get_user_state(this, user_id: int) -> int:

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

    async def add_captcha(this, user_id: int, text: str, chat_id: int) -> None:

        cur = this.con.cursor()
        
        """
        First delete old pending captcha

        """
        cur.execute(
            """
            DELETE FROM
                captcha
            WHERE
                (user_id = %(uid)s AND ca_for = %(cid)s)
            """,
            {"uid": user_id, "cid": chat_id},
        )

        cur.execute(
            """
            INSERT
                INTO captcha
                    (user_id, ca_for, ca_text, ca_time)
                VALUES
                    (%(in_user_id)s, %(in_ca_for)s, %(in_ca_text)s, %(in_ca_time)s)
            """,
            {
                "in_user_id": user_id,
                "in_ca_for": chat_id,
                "in_ca_text": text.lower(),
                "in_ca_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

        cur.execute(
            """
            UPDATE
                users_stats
            SET
                state_for_chat = %(cid)s
            WHERE
                user_id = %(uid)s
            """,
            {"uid": user_id, "cid": chat_id},
        )

        this.con.commit()

    async def solve_captcha(this, user_id: int, text: str) -> Captcha:

        cur = this.con.cursor()
        ret_captcha = Captcha()
        try:
            cur.execute(
                """
                SELECT
                    id, ca_for, ca_time
                FROM
                    captcha
                WHERE
                    (ca_text = %(t)s AND user_id = %(uid)s AND ca_approved = false)
                """,
                {"t": text.lower(), "uid": user_id},
            )
            row = cur.fetchone()
        except Exception as e:
            ret_captcha.error = True,
            ret_captcha.error_msg = str(e)
            return ret_captcha

        if not row:
            ret_captcha.found = False
            return ret_captcha
        row = list(row)
        now = int(datetime.now().timestamp())

        if row:
            ret_captcha.id = row[0]
            ret_captcha.for_chat = row[1]
            ret_captcha.found = True

        ret_captcha.created_at = row[2]

        timediff = now - int(ret_captcha.created_at.timestamp())

        if timediff > this.captcha_timer:
            ret_captcha.expired = True
            ret_captcha.text = text

            return ret_captcha
        """ Delete captcha from table after correct answer """
        cur.execute(
            """
            DELETE FROM
                captcha
            WHERE
                (ca_text = %(t)s AND user_id = %(uid)s)
            """,
            {"t": text.lower(), "uid": user_id},
        )
        this.con.commit()

        return ret_captcha

    async def refresh_captcha(this, id: int, new_text: str) -> None:
        """Updates expired captcha"""

        cur = this.con.cursor()
        cur.execute(
            """
            UPDATE
                captcha
            SET
                ca_text = %(ntext)s, ca_time = %(ntime)s
            WHERE
                (id = %(id)s)
            """,
            {
                "ntext": new_text.lower(),
                "ntime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "id": id,
            },
        )
        this.con.commit()

    async def get_pending_chats(this, user_id: int) -> list:
        """Returns a list of chats that have pending\not approved requests"""

        cur = this.con.cursor()
        cur.execute(
            """
            SELECT
                ca_for
            FROM
                captcha
            WHERE
                (user_id = %(uid)s AND ca_approved = false)
            """,
            {"uid": user_id},
        )

        rows = cur.fetchall()
        if len(rows) > 1:
            # Change list[tuple[int]] to list[int],
            # remove duplicates and return list
            chats = list(set([row[0] for row in rows]))
        elif len(rows) < 1:
            chats = []
        else:
            chats = list(rows[0])  # Tuple to list

        return chats

    async def renew_captcha(this, user_id: int, text: str) -> None:

        cur = this.con.cursor()
        cur.execute(
            """
            UPDATE
                captcha
            SET
                ca_text = %(ntext)s, ca_time = %(ntime)s
            FROM
                (SELECT
                     state_for_chat
                 FROM
                     users_stats
                 WHERE
                     user_id = %(sub_uid)s
                )
            AS usstat
            WHERE
                user_id = %(uid)s AND ca_for = usstat.state_for_chat
            """,
            {
                "ntext": text.lower(),
                "ntime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sub_uid": user_id,
                "uid": user_id,
            },
        )

        this.con.commit()

    async def get_pending_for(this, user_id: int) -> int:

        cur = this.con.cursor()
        cur.execute(
            """
            SELECT
                state_for_chat
            FROM
                users_stats
            WHERE
                user_id = %(uid)s
            """,
            {"uid": user_id},
        )

        chat_id = cur.fetchone()[0]  # Returns tuple
        return chat_id

    async def delete_all_from_chat(this, chat_id: int) -> None:

        """
        Remove all captcha for a specific chat.
        To not handle invalid requests in case we get kicked out from chat/channel

        """

        cur = this.con.cursor()
        cur.execute(
            """
            DELETE FROM
                captcha
            WHERE
                ca_for = %(cid)s
            """,
            {"cid": chat_id},
        )

        this.con.commit()

    async def chat_ca_handle_status(this, chat_id: int) -> bool:

        # @todo Something is wrong with this function,
        # needs to refactor
        cur = this.con.cursor()
        cur.execute(
            """
            SELECT
                stopped
            FROM
                chats_stats
            WHERE
                chat_id = %(cid)s
            """,
            {"cid": chat_id},
        )
        row = cur.fetchone()
        return row[0]

    async def start_handling(this, chat_id: int) -> None:

        cur = this.con.cursor()
        cur.execute(
            """
            UPDATE
                chats_stats
            SET
                stopped = 'yes'
            WHERE
                chat_id = %(cid)s
            """,
            {"cid": chat_id},
        )
        this.con.commit()

    async def stop_handling(this, chat_id: int) -> None:

        cur = this.con.cursor()
        cur.execute(
            """
            UPDATE
                chats_stats
            SET
                stopped = 'no'
            WHERE
                chat_id = %(cid)s
            """,
            {"cid": chat_id},
        )
        this.con.commit()



    """
    # todo Functions not yet implemented in the bot main code

    """

    async def ban_user(this, user_id: int) -> None:
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
        this.con.commit()

    async def unban_user(this, user_id: int) -> None:
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
        this.con.commit()

    def is_user_admin(this, user_id: int) -> bool:
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
        row = list(row)

        return row[0]

    async def edit_admin(this, user_id: int, val: str) -> None:
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
        this.con.commit()

    def is_user_banned(this, user_id: int) -> bool:
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

    def get_users_count(this) -> int:
        cur = this.con.cursor()
        cur.execute("""SELECT * FROM users_stats""")
        rows = cur.fetchall()
        rows = list(rows)
        return len(rows)

    def get_user_chats(this, user_id: int) -> list[int]:
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
        elif len(row[0]) == 0:
            return []
        else:
            return row[0]

    def get_user(this, user_id: int) -> list[str]:
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
        """
            Removing unnecessary whitespaces,
            because table columns are in the CHAR64 format
        """
        for i in range(0, len(row)):
            try:
                row[i] = row[i].strip()
            except Exception:
                pass
        return row

    def update_limiter(this, user_id: int) -> None:

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
        this.con.commit()

    def update_chat_limiter(this, chat_id: int) -> None:

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
        this.con.commit()

    def get_user_limits(this, user_id: int) -> list[str]:

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

    def get_chat_limits(this, chat_id: int) -> list[str]:
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

    def get_chat_members(this, chat_id: int) -> list[list[Union[int, str]]]:
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
        Stripping unnecessary whitespaces.
        Check this.start() for more info.

        """
        _names = [_name.strip() for _name in [row[1] for row in rows]]
        _domains = [_domain.strip() for _domain in [row[2] for row in rows]]

        result = []
        for i in range(0, len(_ids)):
            result.append([_ids[i], _names[i], _domains[i]])
        return result

    """
    # todo end

    """
