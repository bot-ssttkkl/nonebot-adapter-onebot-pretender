from nonebot import logger


def init_ob11_pretender_impl():
    try:
        from . import red  # noqa: F401
    except ImportError as e:
        logger.opt(exception=e).debug("Failed to Import OB11 Red Pretender")
