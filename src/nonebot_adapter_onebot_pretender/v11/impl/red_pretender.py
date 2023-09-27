from pathlib import Path
from typing import Type, Dict

from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot as OB11Bot, ActionFailed
from nonebot.adapters.onebot.v11 import Message as OB11Msg, MessageSegment as OB11MS
from nonebot.adapters.onebot.v11 import event as ob11_event
from nonebot.adapters.onebot.v11.event import Sender
from nonebot.adapters.red import Adapter as RedAdapter, Bot as RedBot
from nonebot.adapters.red import Message as RedMsg, MessageSegment as RedMS
from nonebot.adapters.red import event as red_event
from nonebot.adapters.red.api.model import ChatType

from ..factory import register_ob11_pretender
from ..pretender import OB11Pretender, api_call_handler, event_handler


@register_ob11_pretender(RedAdapter)
class RedOB11Pretender(OB11Pretender[RedAdapter, RedBot, red_event.Event]):
    @classmethod
    def get_actual_adapter_type(cls) -> Type[RedAdapter]:
        return RedAdapter

    def convert_ob11_msg(self, ob11_msg: OB11Msg) -> RedMsg:
        msg = RedMsg()
        for m in ob11_msg:
            if m.type == "text":
                msg.append(RedMS.text(m.data["text"]))
            elif m.type == "at":
                if m.data["qq"] == "all":
                    msg.append(RedMS.at_all())
                else:
                    msg.append(RedMS.at(m.data["qq"]))
            elif m.type == "image":
                file = m.data["file"]
                if isinstance(file, str):
                    file = Path(file)
                msg.append(RedMS.image(file))
            else:
                logger.warning(f"暂不支持 {m.type} 类型消息转换 (OB11 -> Red)")
        return msg

    def convert_red_msg(self, red_msg: RedMsg) -> OB11Msg:
        msg = OB11Msg()
        for m in red_msg:
            if m.type == "text":
                msg.append(OB11MS.text(m.data["text"]))
            elif m.type == "at":
                msg.append(OB11MS.at(m.data["user_id"]))
            elif m.type == "at_all":
                msg.append(OB11MS.at("all"))
            elif m.type == "image":
                msg.append(OB11MS.image(m.data["path"]))
            else:
                logger.warning(f"暂不支持 {m.type} 类型消息转换 (Red -> OB11)")
        return msg

    @api_call_handler("send_msg")
    async def handle_send_msg(self, bot: OB11Bot, data: Dict) -> Dict:
        msg = data["message"]
        if isinstance(msg, OB11Msg):
            msg = self.convert_ob11_msg(msg)

        if data.get("message_type") == "private":
            chat = ChatType.FRIEND
            target = data.get("user_id")
        elif data.get("message_type") == "group":
            chat = ChatType.GROUP
            target = data.get("group_id")
        elif data.get("user_id"):
            chat = ChatType.FRIEND
            target = data.get("user_id")
        elif data.get("group_id"):
            chat = ChatType.GROUP
            target = data.get("group_id")
        else:
            raise ValueError("请传入正确的参数")

        res = await self.adapter.get_actual_bot(bot).send_message(
            chat,
            target,
            msg
        )
        logger.info("send_msg: " + res.json())
        return {
            "message_id": int(res.msgId)
        }

    @api_call_handler("send_group_msg")
    async def handle_send_group_msg(self, bot: OB11Bot, data: Dict) -> Dict:
        msg = data["message"]
        if isinstance(msg, OB11Msg):
            msg = self.convert_ob11_msg(msg)
        res = await self.adapter.get_actual_bot(bot).send_group_message(
            data["group_id"],
            msg
        )
        logger.info("send_group_msg: " + res.json())
        return {
            "message_id": int(res.msgId)
        }

    @api_call_handler("send_private_msg")
    async def handle_send_private_msg(self, bot: OB11Bot, data: Dict) -> Dict:
        msg = data["message"]
        if isinstance(msg, OB11Msg):
            msg = self.convert_ob11_msg(msg)
        res = await self.adapter.get_actual_bot(bot).send_friend_message(
            data["user_id"],
            msg
        )
        logger.info("send_private_msg: " + res.json())
        return {
            "message_id": int(res.msgId)
        }

    @event_handler(red_event.GroupMessageEvent)
    async def handle_group_message_event(self, bot: RedBot,
                                         event: red_event.GroupMessageEvent) -> ob11_event.GroupMessageEvent:
        logger.info("GroupMessageEvent: " + event.json())
        msg = self.convert_red_msg(event.message)
        ori_msg = self.convert_red_msg(event.original_message)
        return ob11_event.GroupMessageEvent(
            time=int(event.msgTime or "0"),
            self_id=int(bot.self_id or "0"),
            post_type="message",
            sub_type="normal",
            user_id=int(event.senderUin or "0"),
            message_id=int(event.msgId or "0"),
            message=msg,
            original_message=ori_msg,
            raw_message=ori_msg.extract_plain_text(),
            font=0,
            sender=Sender(
                user_id=int(event.senderUin or "0"),
                nickname=event.sendMemberName
            ),
            message_type="group",
            group_id=int(event.peerUin),
            to_me=event.to_me,
            reply=None,
            anonymous=None)

    @event_handler(red_event.PrivateMessageEvent)
    async def handle_private_message_event(self, bot: RedBot,
                                           event: red_event.PrivateMessageEvent) -> ob11_event.PrivateMessageEvent:
        logger.info("PrivateMessageEvent: " + event.json())
        msg = self.convert_red_msg(event.message)
        ori_msg = self.convert_red_msg(event.original_message)
        return ob11_event.PrivateMessageEvent(
            time=int(event.msgTime or "0"),
            self_id=int(bot.self_id or "0"),
            post_type="message",
            sub_type="normal",
            user_id=int(event.senderUin or "0"),
            message_id=int(event.msgId or "0"),
            message=msg,
            original_message=ori_msg,
            raw_message=ori_msg.extract_plain_text(),
            font=0,
            sender=Sender(
                user_id=int(event.senderUin or "0"),
                nickname=event.sendMemberName
            ),
            message_type="private",
            to_me=event.to_me,
            reply=None,
        )
