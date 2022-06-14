# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022

from os import environ
from typing import Union

from urllib.parse import urlparse
from configparser import ConfigParser

from httpx import get as httpx_get


class BotConfig:

    def __init__(this) -> None:

        this.postgresql_url = environ.get("DATABASE_URL")
        this.bot_token = environ.get("BOT_TOKEN")
        this.config = ConfigParser()
        this.config.read("eva/configs/config.ini")
        if not this.config.has_section("bot") and not this.bot_token:
            raise Exception(
                'Token not found: Missing "BOT_TOKEN" env var or "config.ini" file'
            )

        if not this.config.has_section("database") and not this.postgresql_url:
            raise Exception('Database params not found: \
Missing "DATABASE_URL" env var or "config.ini" file')

    def get_connect_params(this) -> list[str]:

        if not this.postgresql_url:
            dbname = this.config.get("database", "db")
            dbuser = this.config.get("database", "user")
            dbpass = this.config.get("database", "password")
            dbhost = this.config.get("database", "host")
            dbport = this.config.get("database", "port")
        else:
            pg_url = urlparse(this.postgresql_url)
            dbname = pg_url.lstrip("/")
            dbuser = pg_url.username
            dbpass = pg_url.password
            dbhost = pg_url.hostname
            dbport = pg_url.port

        return [dbname, dbuser, dbpass, dbhost, dbport]

    def get_bot_token(this) -> str:

        return (this.config.get("bot", "token")
                if not this.bot_token else this.bot_token)

    def get_bot_username(this) -> str:

        _api_response = httpx_get(
            "https://api.telegram.org/bot{}/getMe".format(
                this.get_bot_token()))
        return _api_response.json().get("result").get("username")

    def is_valid_token(this, token = str) -> bool:
        _api_response = httpx_get(
            "https://api.telegram.org/bot{}/getMe".format(token))
        return _api_response.json().get("result").get("ok")

    def get_bot_id(this) -> int:

        return int(this.get_bot_token().split(":")[0])

    def get_owner_id(this) -> int:

        return this.config.getint("bot", "admin")

    def get_api_params(this) -> list[Union[int, str]]:

        _api_id: int = this.config.getint("api", "id")
        _api_hash: str = this.config.get("api", "hash")
        return [_api_id, _api_hash]

    def get_limits(this, key: str) -> str:

        return this.config.get("limits", key)

    def get_captcha_settings(this) -> list[int]:

        length: int = this.config.getint("captcha", "lenght")
        width: int = this.config.getint("captcha", "width")
        height: int = this.config.getint("captcha", "height")

        return [length, width, height]

    def get_spamwatch_token(this) -> str:

        return this.config.get("spamwatch", "token")
