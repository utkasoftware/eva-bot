# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022


from sys import version_info, setprofile
from os import environ


__dev_mode = environ.get("BOT_DEV_MODE", "False").lower() in ("true", "1", "t")
if __dev_mode:
    from .tests import traceit

    setprofile(traceit.tracefunc)


if version_info < (3, 10, 0):
    print("Eva needs a Python version of at least 3.10 to work correctly.")
else:
    if __package__ != "eva":
        print(
            "Error: you cannot run this as a script; you must execute as a package"
        )
    else:
        try:
            from . import eva
        except ModuleNotFoundError:
            print("Error: Please install missing package dependencies")
            raise
        else:
            if __name__ == "__main__":
                eva.start()
