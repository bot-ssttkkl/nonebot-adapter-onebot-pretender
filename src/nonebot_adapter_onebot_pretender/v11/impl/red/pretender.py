import json
from pathlib import Path
from base64 import b64decode
from typing import Dict, Type, Union, Optional

from nonebot.utils import logger_wrapper
from nonebot.adapters.red import Bot as RedBot
from nonebot.adapters.red import Message as RedMsg
from nonebot.adapters.red import event as red_event
from nonebot.adapters.onebot.v11 import ActionFailed
from nonebot.adapters.red import Adapter as RedAdapter
from nonebot.adapters.red import MessageSegment as RedMS
from nonebot.adapters.onebot.v11 import Message as OB11Msg
from nonebot.adapters.onebot.v11 import event as ob11_event
from nonebot.adapters.onebot.v11.event import Reply, Sender
from nonebot.adapters.onebot.v11 import MessageSegment as OB11MS

from ...factory import register_ob11_pretender
from ...pretender import OB11Pretender, event_handler, api_call_handler
from ....data.ob11_msg import OB11MsgModel, load_ob11_msg, save_ob11_msg

log = logger_wrapper("OneBot V11 Pretender (RedProtocol)")


@register_ob11_pretender(RedAdapter)
class RedOB11Pretender(OB11Pretender[RedAdapter, RedBot, red_event.Event]):
    @classmethod
    def get_actual_adapter_type(cls) -> Type[RedAdapter]:
        return RedAdapter

    @classmethod
    def log(cls, level: str, content: str, exc: Optional[BaseException] = None):
        log(level, content, exc)

    def convert_outgoing_msg(self, outgoing: OB11Msg) -> RedMsg:
        msg = RedMsg()
        for m in outgoing:
            if m.type == "text":
                msg.append(RedMS.text(m.data["text"]))
            elif m.type == "at":
                if m.data["qq"] == "all":
                    msg.append(RedMS.at_all())
                else:
                    msg.append(RedMS.at(m.data["qq"]))
            elif m.type == "face":
                msg.append(RedMS.face(m.data["id"]))
            elif m.type == "image":
                file = m.data["file"]
                if isinstance(file, str):
                    if file.startswith("base64://"):
                        file = b64decode(file.removeprefix("base64://"))
                    else:
                        file = Path(file)
                msg.append(RedMS.image(file))
            elif m.type == "video":
                file = m.data["file"]
                if isinstance(file, str):
                    file = Path(file)
                msg.append(RedMS.video(file))
            elif m.type == "record":
                file = m.data["file"]
                if isinstance(file, str):
                    file = Path(file)
                msg.append(RedMS.voice(file))
            elif m.type == "reply":
                msg.append(
                    RedMS.reply(
                        m.data.get("seq"),
                        m.data.get("id"),
                        m.data.get("qq"),
                    )
                )
            else:
                log("WARNING", f"暂不支持 {m.type} 类型消息转换 (OB11 -> Red)")
        return msg

    def convert_incoming_msg(self, incoming: RedMsg) -> OB11Msg:
        msg = OB11Msg()
        for m in incoming:
            if m.type == "text":
                msg.append(OB11MS.text(m.data["text"]))
            elif m.type == "at":
                msg.append(
                    OB11MS(
                        "at",
                        {"qq": str(m.data["user_id"]), "name": m.data.get("user_name")},
                    )
                )
            elif m.type == "at_all":
                msg.append(OB11MS.at("all"))
            elif m.type == "face":
                msg.append(OB11MS("face", {"id": str(m.data["face_id"])}))
            elif m.type == "market_face":
                msg.append(
                    OB11MS(
                        "image",
                        {
                            "file": m.data["emoji_id"] + "_aio.image",
                            "url": "file://" + m.data["static_path"],
                        },
                    )
                )
            elif m.type == "image":
                msg.append(
                    OB11MS(
                        "image",
                        {
                            "file": m.data["md5"] + ".image",
                            "url": "file://" + m.data["path"],
                        },
                    )
                )
            elif m.type == "video":
                msg.append(
                    OB11MS(
                        "video",
                        {
                            "file": m.data["name"],
                            "url": "file://" + m.data["path"],
                            "cover": "file://" + m.data["thumb_path"],
                        },
                    )
                )
            elif m.type == "voice":
                msg.append(
                    OB11MS(
                        "record",
                        {"file": m.data["name"], "url": "file://" + m.data["path"]},
                    )
                )
            elif m.type == "reply":
                msg.append(
                    OB11MS(
                        "reply",
                        {
                            "id": str(m.data["msg_id"]),
                        },
                    )
                )
            elif m.type == "forward":
                msg.append(OB11MS("forward", {"id": str(m.data["id"])}))
            else:
                log("WARNING", f"暂不支持 {m.type} 类型消息转换 (Red -> OB11)")
        return msg

    @api_call_handler()
    async def send_msg(
        self,
        bot: RedBot,
        *,
        message_type: Optional[str] = None,
        user_id: Optional[int] = None,
        group_id: Optional[int] = None,
        message: Union[str, OB11Msg],
        **data: Dict,
    ) -> Dict:
        if message_type == "private":
            return await self.send_private_msg(bot, user_id=user_id, message=message)
        elif message_type == "group":
            return await self.send_group_msg(bot, user_id=group_id, message=message)
        elif user_id:
            return await self.send_private_msg(bot, user_id=user_id, message=message)
        elif group_id:
            return await self.send_group_msg(bot, user_id=group_id, message=message)
        else:
            raise ValueError("请传入正确的参数")

    @api_call_handler()
    async def send_group_msg(
        self, bot: RedBot, *, group_id: int, message: Union[str, OB11Msg], **data: Dict
    ) -> Dict:
        if isinstance(message, str):
            message = OB11Msg(message)
        ob11_msg = message

        message = self.convert_outgoing_msg(message)

        res = await bot.send_group_message(group_id, message)
        await save_ob11_msg(
            res.msgId,
            OB11MsgModel(
                group=True,
                group_id=group_id,
                message_id=int(res.msgId),
                real_id=int(res.msgId),
                message_type="group",
                sender=Sender(
                    nickname=res.sendNickName or res.sendMemberName,
                    user_id=int(bot.self_id),
                ),
                time=int(res.msgTime or "0"),
                message=ob11_msg,
                raw_message=ob11_msg.extract_plain_text(),
            ),
        )
        return {"message_id": int(res.msgId)}

    @api_call_handler()
    async def send_private_msg(
        self, bot: RedBot, *, user_id: int, message: Union[str, OB11Msg], **data: Dict
    ) -> Dict:
        if isinstance(message, str):
            message = OB11Msg(message)
        ob11_msg = message

        message = self.convert_outgoing_msg(message)

        res = await bot.send_friend_message(user_id, message)
        await save_ob11_msg(
            res.msgId,
            OB11MsgModel(
                group=False,
                group_id=None,
                message_id=int(res.msgId),
                real_id=int(res.msgId),
                message_type="private",
                sender=Sender(
                    nickname=res.sendNickName or res.sendMemberName,
                    user_id=int(bot.self_id),
                ),
                time=int(res.msgTime or "0"),
                message=ob11_msg,
                raw_message=ob11_msg.extract_plain_text(),
            ),
        )
        return {"message_id": int(res.msgId)}

    @api_call_handler
    async def get_login_info(self, bot: RedBot, **data: Dict) -> Dict:
        profile = await bot.get_self_profile()
        return {
            "user_id": int(profile.uin or profile.uid or profile.qid),
            "nickname": profile.longNick or profile.nick,
        }

    @api_call_handler()
    async def get_msg(self, bot: RedBot, message_id: int, **data: Dict) -> Dict:
        msg = await load_ob11_msg(str(message_id))
        if msg is not None:
            return json.loads(msg.json(exclude_none=True))
        else:
            raise ActionFailed(msg="消息不存在")

    @event_handler(red_event.GroupMessageEvent)
    async def handle_group_message_event(
        self, bot: RedBot, event: red_event.GroupMessageEvent
    ) -> ob11_event.GroupMessageEvent:
        msg = self.convert_incoming_msg(event.message)
        ori_msg = self.convert_incoming_msg(event.original_message)

        reply = None
        if event.reply and event.reply.replayMsgId:
            reply = await self.get_msg(bot, int(event.reply.replayMsgId))
            if reply is not None:
                reply = Reply.parse_obj(reply)

        await save_ob11_msg(
            event.msgId,
            OB11MsgModel(
                group=True,
                group_id=int(event.peerUin or "0"),
                message_id=int(event.msgId),
                real_id=int(event.msgId),
                message_type="group",
                sender=Sender(
                    nickname=event.sendNickName or event.sendMemberName,
                    user_id=int(event.senderUin or "0"),
                ),
                time=int(event.msgTime or "0"),
                message=msg,
                raw_message=ori_msg.extract_plain_text(),
            ),
        )

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
                nickname=event.sendNickName or event.sendMemberName,
                sex="unknown",
                age=0,
                card=event.sendMemberName,
                role="member",  # todo
                title="",
            ),
            message_type="group",
            group_id=int(event.peerUin),
            to_me=event.to_me,
            reply=reply,
            anonymous=None,
        )

    @event_handler(red_event.PrivateMessageEvent)
    async def handle_private_message_event(
        self, bot: RedBot, event: red_event.PrivateMessageEvent
    ) -> ob11_event.PrivateMessageEvent:
        msg = self.convert_incoming_msg(event.message)
        ori_msg = self.convert_incoming_msg(event.original_message)

        reply = None
        if event.reply and event.reply.replayMsgId:
            reply = Reply.parse_obj(
                await self.get_msg(bot, int(event.reply.replayMsgId))
            )

        await save_ob11_msg(
            event.msgId,
            OB11MsgModel(
                group=False,
                message_id=int(event.msgId),
                real_id=int(event.msgId),
                message_type="private",
                sender=Sender(
                    nickname=event.sendNickName or event.sendMemberName,
                    user_id=int(event.senderUin or "0"),
                ),
                time=int(event.msgTime or "0"),
                message=msg,
                raw_message=ori_msg.extract_plain_text(),
            ),
        )

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
                nickname=event.sendNickName or event.sendMemberName,
                sex="unknown",
                age=0,
            ),
            message_type="private",
            to_me=event.to_me,
            reply=reply,
        )
