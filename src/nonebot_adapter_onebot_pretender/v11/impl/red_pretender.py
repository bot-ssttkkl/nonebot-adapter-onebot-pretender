from typing import Type, Dict

from nonebot.adapters.onebot.v11 import Bot as OB11Bot
from nonebot.adapters.onebot.v11 import event as ob11_event
from nonebot.adapters.red import Adapter as RedAdapter, Bot as RedBot
from nonebot.adapters.red import event as red_event

from ..factory import register_ob11_pretender
from ..pretender import OB11Pretender, api_call_handler, event_handler


@register_ob11_pretender(RedAdapter)
class RedOB11Pretender(OB11Pretender[RedAdapter, RedBot]):
    @classmethod
    def get_actual_adapter_type(cls) -> Type[RedAdapter]:
        return RedAdapter

    @api_call_handler()
    def send_message(self, bot: OB11Bot, data: Dict) -> Dict:
        ...

    @event_handler(red_event.PrivateMessageEvent)
    def private_message_event(self, bot: RedBot,
                              event: red_event.PrivateMessageEvent) -> ob11_event.PrivateMessageEvent:
        ...
