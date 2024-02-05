from copy import copy
from abc import ABC, abstractmethod
from typing_extensions import override
from typing import TYPE_CHECKING, Any, Type, Generic, TypeVar, Optional

from nonebot import Driver
from nonebot.adapters import Bot as BaseBot
from nonebot.adapters import Event as BaseEvent
from nonebot.adapters import Adapter as BaseAdapter
from nonebot.adapters.onebot.v11 import Bot as OB11Bot
from nonebot.adapters.onebot.v11 import Adapter as OB11Adapter

from ..patch_handle_event import patch_event_handle, origin_handle_event

if TYPE_CHECKING:
    from .pretender import OB11Pretender

T_ActualAdapter = TypeVar("T_ActualAdapter", bound=BaseAdapter)
T_ActualBot = TypeVar("T_ActualBot", bound=BaseBot)


class Adapter(OB11Adapter, Generic[T_ActualAdapter, T_ActualBot], ABC):
    @override
    def __init__(self, driver: Driver, **kwargs: Any):
        super().__init__(driver, **kwargs)
        self.pretender = self.get_pretender_type()(self)
        self.actual_adapter = self._create_actual_adapter_with_hack(driver, **kwargs)

    def _setup(self) -> None:
        @patch_event_handle
        async def handle_event(bot: BaseBot, event: BaseEvent) -> bool:
            if bot.self_id in self.actual_adapter.bots:
                handled_event = await self.pretender.handle_event(bot, event)
                if handled_event is None:
                    self.pretender.log(
                        "WARNING",
                        f"No event handler for {type(event).__name__} "
                        f"({self.actual_adapter.get_name()}) found, "
                        f"event was ignored",
                    )
                else:
                    await origin_handle_event(self.bots[bot.self_id], handled_event)
                return True
            else:
                return False

    @classmethod
    @abstractmethod
    def get_pretender_type(
        cls,
    ) -> Type["OB11Pretender[T_ActualAdapter, T_ActualBot]"]: ...

    def get_actual_bot(self, bot: OB11Bot) -> Optional[T_ActualBot]:
        return self.actual_adapter.bots.get(bot.self_id)

    def _create_actual_adapter_with_hack(
        self, driver: Driver, **kwargs: Any
    ) -> T_ActualAdapter:
        pretender_adapter = self

        hacky_driver = copy(driver)

        def bot_connect(bot: T_ActualBot) -> None:
            ob11bot = OB11Bot(pretender_adapter, bot.self_id)
            pretender_adapter.bot_connect(ob11bot)

        hacky_driver._bot_connect = bot_connect

        def bot_disconnect(bot: T_ActualBot) -> None:
            pretender_bot = pretender_adapter.bots.get(bot.self_id)
            assert (
                pretender_bot is not None
            ), f"cannot find pretender bot {bot.self_id} ({bot.type})"
            pretender_adapter.bot_disconnect(pretender_bot)

        hacky_driver._bot_disconnect = bot_disconnect

        return self.pretender.get_actual_adapter_type()(hacky_driver, **kwargs)

    @override
    async def _call_api(self, bot: OB11Bot, api: str, **data: Any) -> Any:
        return await self.pretender.handle_api_call(bot, api, **data)
