# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022

import logging
import coloredlogs
import verboselogs


_default_format = (
    "%(asctime)s %(filename)s:%(funcName)s:%(lineno)d %(levelname)s %(message)s"
)
DEFAULT_LEVEL = "INFO"
logger = verboselogs.VerboseLogger(__name__)
logger.DEFAULT_LEVEL = DEFAULT_LEVEL
coloredlogs.install(level=DEFAULT_LEVEL, fmt=_default_format)
