import logging
import sys

_configured = False

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    global _configured
    if not _configured:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        root = logging.getLogger()
        root.addHandler(handler)
        root.setLevel(level)
        _configured = True

    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger