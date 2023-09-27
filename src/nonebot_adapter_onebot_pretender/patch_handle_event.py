from functools import wraps
from typing import Callable, TYPE_CHECKING, List, Awaitable

from nonebot import message

if TYPE_CHECKING:
    from nonebot import Bot
    from nonebot.internal.adapter import Event

    T_EventHandler = Callable[[Bot, Event], Awaitable[bool]]

origin_handle_event = message.handle_event

_event_handler: List["T_EventHandler"] = []


def patch_event_handler(handler: "T_EventHandler") -> "T_EventHandler":
    _event_handler.append(handler)
    return handler


@wraps(origin_handle_event)
async def handle_event(bot: "Bot", event: "Event") -> None:
    for handler in _event_handler:
        if await handler(bot, event):
            return
    await origin_handle_event(bot, event)


message.handle_event = handle_event

__all__ = ("patch_event_handler", "origin_handle_event")
