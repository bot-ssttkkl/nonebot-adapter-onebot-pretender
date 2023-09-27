from abc import abstractmethod, ABCMeta
from typing import TypeVar, Generic, Type, Any, Callable, TYPE_CHECKING, Dict, Optional, Tuple

from nonebot.adapters import Adapter as BaseAdapter, Bot as BaseBot, Event as BaseEvent, Message as BaseMessage
from nonebot.adapters.onebot.v11 import Bot as OB11Bot, Event as OB11Event, ApiNotAvailable

if TYPE_CHECKING:
    from .adapter import Adapter as OB11PretenderAdapter

T_ActualAdapter = TypeVar("T_ActualAdapter", bound=BaseAdapter)
T_ActualBot = TypeVar("T_ActualBot", bound=BaseBot)
T_ActualEvent = TypeVar("T_ActualEvent", bound=BaseEvent)

T_ApiHandler = Callable[["OB11Pretender", OB11Bot, Dict], Any]
T_EventHandler = Callable[["OB11Pretender", T_ActualBot, T_ActualEvent], OB11Event]


class OB11PretenderMeta(ABCMeta):
    def __new__(mcls, name: str, base: Tuple[type, ...], namespace: dict, *args, **kwargs):
        api_call_handlers = {}

        for item in namespace.values():
            if getattr(item, "__api_call_handler__", False):
                api_call_handlers[item.__api_call_name__] = item

        namespace["_api_call_handler_mapping"] = api_call_handlers

        event_handlers = {}

        for item in namespace.values():
            if getattr(item, "__event_handler__", False):
                event_handlers[item.__event_type__] = item

        namespace["_event_handler_mapping"] = event_handlers

        return super().__new__(mcls, name, base, namespace, **kwargs)


class OB11Pretender(Generic[T_ActualAdapter, T_ActualBot, T_ActualEvent], metaclass=OB11PretenderMeta):
    _api_call_handler_mapping: Dict[str, T_ApiHandler]
    _event_handler_mapping: Dict[Type[BaseEvent], T_EventHandler]

    def __init__(self, adapter: "OB11PretenderAdapter[T_ActualAdapter, T_ActualBot]"):
        self.adapter = adapter

    @classmethod
    @abstractmethod
    def get_actual_adapter_type(cls) -> Type[T_ActualAdapter]:
        ...

    async def handle_api_call(self, bot: OB11Bot, api: str, **data: Any) -> Any:
        handler = self._api_call_handler_mapping.get(api)
        if handler is None:
            raise ApiNotAvailable

        return await handler(self, bot, data)

    async def handle_event(self, bot: T_ActualBot, event: T_ActualEvent) -> Optional[OB11Event]:
        handler = None
        for t_event in type(event).mro():
            handler = self._event_handler_mapping.get(t_event)
            if handler is not None:
                break

        if handler is None:
            return None

        return await handler(self, bot, event)


def api_call_handler(api: Optional[str] = None):
    def decorator(func: T_ApiHandler) -> T_ApiHandler:
        func.__api_call_handler__ = True
        func.__api_call_name__ = api or func.__name__

        return func

    return decorator


def event_handler(event_type: Type[BaseEvent]):
    def decorator(func: T_EventHandler) -> T_EventHandler:
        func.__event_handler__ = True
        func.__event_type__ = event_type

        return func

    return decorator
