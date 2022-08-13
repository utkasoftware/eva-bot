# -*- coding: utf-8 -*-


from enum import IntEnum


class States(IntEnum):

    START = 0
    WAIT_FOR_ANSWER = 1
    SELECT_CHAT = 2
    GROUP_WAIT_FOR_CMD = 3
    FEEDBACK_WAIT_FOR_ANSWER = 4
