# -*- coding: utf-8 -*-

from telethon import TelegramClient


from .core.config   import Config as Config
from .core.security import (
    BotManage as BotManage,
    UserState as UserState
)

from .structs import (
    Captcha as Captcha,
    User    as User
)

from .core.storages import (
    UserStorage as UserStorage,
    ChatStorage as ChatStorage,
    CaptchaStorage as CaptchaStorage
)
from .modules import (
    Language as Language,
    logger   as logger
)

from .wrappers import CaptchaWrapper
from . import utils


config = Config()
usc = UserState()  # User states control
states = usc.states  # States list

bot_manage = BotManage()

user_storage = UserStorage()
chat_storage = ChatStorage()
captcha_storage = CaptchaStorage()

local = Language.loadv2(config.get_default_language())

captcha_wrapper = CaptchaWrapper()

# api_id, api_hash = BotConfig.get_api_params()

bot = TelegramClient(
    __package__,
    *config.get_api_params(),
    flood_sleep_threshold=30
)

