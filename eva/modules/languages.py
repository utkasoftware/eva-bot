# -*- coding: utf-8 -*-
# © Uli Sotschok, 2019
# https://stackoverflow.com/a/57620899


from dataclasses import make_dataclass, field
from typing import NoReturn
from json import (
    JSONDecodeError,
    load as json_load
)

from . import logger



"""

class Local:
    name - local_<lang_code>


"""


class Language:

    def __init__(this, lang_dict: dict) -> None:

        this.lang_dict = lang_dict
        this.__dict__.update(this.lang_dict)

    @classmethod
    def load_default(cls) -> dict:
        with open(
            "eva/../langs/default.json",
            "r", encoding="utf-8"
        ) as raw_json:
            return json_load(raw_json)

    @classmethod
    def generate_local_dtcls(cls,
        lang_name: str,
        _locals: dict) -> type:

        _fields = []
        for k,v in _locals.items():
            _fields.append(
                (k, str, field(default=v))
            )

        return make_dataclass(
            "local_{}".format(lang_name),
            _fields,
            namespace={
                "_name": lambda this: this.__class__.__name__
            }
        )()

    @staticmethod
    def load(language_name: str | None = None) -> "Language" | NoReturn:

        if language_name is not None:

            language_name += ".json"
            try:
                with open(language_name, encoding="utf-8") as raw_json:
                    lang_json = json_load(raw_json)

            except FileNotFoundError:
                logger.warn(
                    "Language file {} not found; loading default file".format(
                        language_name))

                with open("eva/../langs/default.json", "r",
                          encoding="utf-8") as raw_json:
                    lang_json = json_load(raw_json)

            except JSONDecodeError:
                logger.fatal(
                    "Something went wrong with language file {}".format(
                        language_name))
                raise

        else:
            with open("eva/../langs/default.json", "r",
                      encoding="utf-8") as raw_json:
                lang_json = json_load(raw_json)

        return Language(lang_json)

    @staticmethod
    def loadv2(lang_fn: str | None = None) -> type:
        if not lang_fn:
            default_dict = Language.load_default()
            return Language.generate_local_dtcls("default", default_dict)

        fn = lang_fn + ".json"

        try:
            with open(
                "eva/../langs/{}".format(fn),
                "r", encoding="utf-8") as raw_json:
                lang_json = json_load(raw_json)

        except FileNotFoundError:
            logger.warn(
                "Language file '{}' not found; loading default file".format(
                    fn
                )
            )
            lang_json = Language.load_default()
            lang_fn = "default"

        except JSONDecodeError:
            logger.fatal(
                "Something went wrong with language file {}".format(
                    fn
                )
            )
            raise

        return Language.generate_local_dtcls(lang_fn, lang_json)
