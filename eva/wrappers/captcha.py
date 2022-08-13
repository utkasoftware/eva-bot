# -*- coding: utf-8 -*-


from string import (
    ascii_letters,
    digits
)

from random import choice
from captcha.image import ImageCaptcha

from eva.structs import Captcha


class CaptchaWrapper:

    """
    Simple captcha generator

    """

    def __init__(this) -> None:

        this.__chars = digits + ascii_letters

    def update_chars(this, chars: list | str) -> None:
        this.__chars = chars

    def generate(this,
        length: int = 5,
        width:  int = 250,
        height: int = 180) -> Captcha:

        text = []
        for _ in range(length):
            text.append(choice(this.__chars))  # nosec

        image_obj = ImageCaptcha(width=width, height=height)
        text = "".join(text)
        image = image_obj.generate(text)

        return Captcha(
            text=text,
            image=image,
            length=length,
            height=height,
            width=width
        )
