# -*- coding: utf-8 -*-


from os import environ
from typing import Union, NoReturn
from string import capwords
from urllib.parse import urlparse

from configparser import ConfigParser

from httpx import get as httpx_get

from eva.structs import SqlConnectParams
from eva.modules import Singleton

from .errors import (
    ConfigMissingError,
    InvalidTokenError
)


class Config(metaclass=Singleton):

    def __init__(this) -> None:

        this.postgresql_url = environ.get("DATABASE_URL")
        this.bot_token = environ.get("BOT_TOKEN")
        this._config = ConfigParser()
        this._config.read("config.ini")

        if not this._config.has_section("bot") and not this.bot_token:
            raise ConfigMissingError(
                'Token not found: Missing "BOT_TOKEN" env var or "config.ini" file'
            )

        if not this._config.has_section("database") and not this.postgresql_url:
            raise ConfigMissingError(
                (
                    'Database params not found: '
                    'Missing "DATABASE_URL" env var or "config.ini" file'
                )
            )

        for section in this._config.sections():
            if hasattr(this, capwords(section)):
                # We have a subclass with a custom implementation of section
                this.__dict__[section] = getattr(
                    this,
                    capwords(section)
                    )(
                        dict(this._config.items(section))
                    )
                continue

            this.__dict__[section] = BaseSection(
                section,
                dict(this._config.items(section))
            )



    def get_connect_params(this) -> SqlConnectParams:

        if not this.postgresql_url:

            dbname = this.database.db
            dbuser = this.database.user
            dbpass = this.database.password
            dbhost = this.database.host
            dbport = this.database.port
        else:
            pg_url = urlparse(this.postgresql_url)
            dbname = pg_url.lstrip("/")
            dbuser = pg_url.username
            dbpass = pg_url.password
            dbhost = pg_url.hostname
            dbport = pg_url.port

        return SqlConnectParams(dbname, dbuser, dbpass, dbhost, dbport)

    def get_bot_token(this) -> str:
        return this.bot.token if not this.bot_token else this.bot.token

    def get_bot_username(this) -> str:
        return this.bot.username

    def get_bot_id(this) -> int:
        return this.bot.id

    def get_owner_id(this) -> int:
        return this.bot.admin

    def get_api_params(this) -> list[int, str]:

        return [
            int(this.api.id),
            this.api.hash
        ]

    def get_limits(this, key: str) -> str:
        return this._config.get("limits", key)

    def get_captcha_settings(this) -> list[int]:

        return [
            int(this.captcha.lenght),
            int(this.captcha.width),
            int(this.captcha.height)
        ]

    def get_spamwatch_token(this) -> str:
        return this.spamwatch.token

    def get_default_language(this) -> str:
        return this.languages.default


    class Bot:

        def __init__(this, section: dict) -> None:
            this.section = section
            this._me = None
            this.validate_token(this.token)


        @property
        def admin(this) -> int:
            return int(
                this.section.get("admin")
            )

        @property
        def token(this) -> str:
            return this.section.get("token")

        # INI end

        @property
        def id(this) -> int:
            return int(
                this.section.get("token").split(":")[0]
            )

        @property
        def username(this) -> str:
            return this._me.get("username")

        def validate_token(this, token: str) -> None | NoReturn:
            resp = httpx_get("https://api.telegram.org/bot{}/getMe".format(token))
            if resp.json().get("ok"):
                this._me = resp.json().get("result")
                return

            raise InvalidTokenError(token, resp.text)


    class Whitelist:

        def __init__(this, section: dict) -> None:
            this.section = section

        @property
        def on(this) -> bool:
            return str(this.section.get("on")).lower() \
            in ["true", "1", "on", "yes", "y"]

        @property
        def chat(this) -> int:
            return int(
                this.section.get("chat")
            )


class BaseSection:

    def __init__(this,
        section_name: str,
        section_data: dict
        ) -> None:

        for key, value in section_data.items():
            this.__dict__[key] = value


