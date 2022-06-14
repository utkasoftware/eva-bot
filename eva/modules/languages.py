# cython: language_level=3
# -*- coding: utf-8 -*-
# © Uli Sotschok, 2019
# https://stackoverflow.com/a/57620899

from __future__ import annotations


from typing import NoReturn
import json

from eva.modules import logger

class Language:

    def __init__(this, lang_dict: dict) -> None:

        this.lang_dict = lang_dict
        this.__dict__.update(this.lang_dict)

    @staticmethod
    def load(language_name: str | None = None) -> Language | NoReturn:

        if language_name is not None:

            language_name += ".json"
            try:
                with open(language_name) as raw_json:
                    lang_json = json.load(raw_json)

            except FileNotFoundError:
                logger.warn(
                    "Language file {} not found; loading default file".format(
                        language_name
                    )
                )

                with open("eva/langs/default.json", "r") as raw_json:
                    lang_json = json.load(raw_json)

            except json.decoder.JSONDecodeError:
                logger.fatal(
                    "Something went wrong with language file {}".format(language_name)
                )
                raise

        else:
            with open("eva/langs/default.json", "r") as raw_json:
                lang_json = json.load(raw_json)

        return Language(lang_json)
