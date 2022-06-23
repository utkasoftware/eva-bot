# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022

from datetime import datetime

from eva.structs import User
from eva.structs import Captcha
from eva.wrappers import Storage

class CaptchaStorage(Storage):

    def __init__(this):
        super().__init__()
        this.__create()
        this.captcha_timer = 60

    def __create(this):
        cur = this.con.cursor()
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
        this.complete_transaction()

    async def add_captcha(
        this, user_id: int, text: str, chat_id: int) -> None:

        cur = this.con.cursor()

        # First delete old pending captcha
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

        this.complete_transaction()

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
            ret_captcha.error = (True,)
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
        this.complete_transaction()
        return ret_captcha

    async def refresh_captcha(this, id: int, new_text: str):
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
        this.complete_transaction()

    async def get_pending_chats_for(this, user_id: int) -> [int]:
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

    async def get_pending_chat_for(this, user_id: int) -> int:
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

        this.complete_transaction()

    async def delete_all_captcha_for(this, chat_id: int) -> None:
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

        this.complete_transaction()

