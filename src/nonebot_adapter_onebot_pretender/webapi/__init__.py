from nonebot import get_driver
from nonebot.internal.driver import ReverseDriver

if not isinstance(get_driver(), ReverseDriver):
    raise RuntimeError("需要使用反向驱动器")
