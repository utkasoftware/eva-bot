import os
import importlib

from .. import logger


__all__: list[str] = []
for _handler in os.listdir(os.path.dirname(__file__)):
    if _handler.startswith("_") or not _handler.endswith(".py"):
        continue

    _handler = _handler.replace(".py", "")
    importlib.import_module(
        ".{}".format(_handler),
        __name__
    )
    try:
        globals()[_handler] = getattr(
            globals()[_handler],
          "{}__cmd".format(_handler)
        )
    except AttributeError as attre:
        logger.warn("cant dynload {0}__cmd from {0}, skipping".format(
            _handler)
        )
        __all__ = [h for h in __all__ if h != _handler]
        continue
            
    __all__.append(_handler)
del _handler
del importlib
del os
