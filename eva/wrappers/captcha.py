# -*- coding: utf-8 -*-
#    Eva Telegram Bot (https://t.me/storoxbot)
#    2020-2022


from random import choice
from captcha.image import ImageCaptcha

from eva.structs import Captcha


class CaptchaWrapper:

    """
    Simple captcha generator

    """

    def __init__(this) -> None:

        this.__chars = [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "a",
            "b",
            "c",
            "d",
            "e",
            "f",
            "g",
            "h",
            "i",
            "j",
            "k",
            "l",
            "m",
            "n",
            "o",
            "p",
            "q",
            "r",
            "s",
            "t",
            "u",
            "v",
            "w",
            "x",
            "y",
            "z",
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "I",
            "J",
            "K",
            "L",
            "M",
            "N",
            "O",
            "P",
            "Q",
            "R",
            "S",
            "T",
            "U",
            "V",
            "W",
            "X",
            "Y",
            "Z",
        ]

        this.Captcha = Captcha

    def generate(this, length: int = 5, width: int = 250, height: int = 180) -> Captcha:

        text = []
        for i in range(length):
            text.append(choice(this.__chars))

        image_obj = ImageCaptcha(width=width, height=height)
        this.Captcha.text = "".join(text)
        this.Captcha.image = image_obj.generate(text)

        return Captcha
