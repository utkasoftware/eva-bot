# -*- coding: utf-8 -*-
# © agf, stackoverflow.com/a/6798042
# 2011


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            # don't want __init__ to be called every time
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

