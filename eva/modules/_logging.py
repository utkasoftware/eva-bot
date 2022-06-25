# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022

import logging
import coloredlogs
import verboselogs


default_format = (
    "%(asctime)s %(filename)s:%(funcName)s:%(lineno)d %(levelname)s %(message)s"
)
logger = verboselogs.VerboseLogger(__name__)
coloredlogs.install(level="INFO", fmt=default_format)

