from functools import wraps
from typing import TYPE_CHECKING, List, Callable, Optional, Awaitable

from nonebot import message

if TYPE_CHECKING:
    from nonebot import Bot
    from nonebot.internal.adapter import Event

    T_EventHandler = Callable[[Bot, Event], Awaitable[bool]]

_origin_handle_event: Optional[Callable[["Bot", "Event"], Awaitable[None]]] = None
_event_handler: List["T_EventHandler"] = []


async def origin_handle_event(bot: "Bot", event: "Event") -> None:
    await _origin_handle_event(bot, event)


def patch_event_handle(handler: "T_EventHandler") -> "T_EventHandler":
    _event_handler.append(handler)
    return handler


def init_patch_handle_event():
    global _origin_handle_event
    _origin_handle_event = message.handle_event

    @wraps(_origin_handle_event)
    async def handle_event(bot: "Bot", event: "Event") -> None:
        for handler in _event_handler:
            if await handler(bot, event):
                return
        await _origin_handle_event(bot, event)

    message.handle_event = handle_event


__all__ = ("patch_event_handle", "origin_handle_event", "init_patch_handle_event")
