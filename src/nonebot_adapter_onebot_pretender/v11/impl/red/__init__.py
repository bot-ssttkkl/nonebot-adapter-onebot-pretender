import json
from pathlib import Path
from base64 import b64decode
from datetime import datetime
from urllib.parse import urlencode, urlunsplit
from typing import Dict, List, Type, Union, Optional

from nonebot.adapters.red import Bot as RedBot
from nonebot.adapters.red import Message as RedMsg
from nonebot.adapters.red import event as red_event
from nonebot.adapters.red.api.model import ChatType
from nonebot.adapters.onebot.v11 import ActionFailed
from nonebot.adapters.red import Adapter as RedAdapter
from nonebot.adapters.red import MessageSegment as RedMS
from nonebot.adapters.onebot.v11 import Message as OB11Msg
from nonebot.utils import DataclassEncoder, logger_wrapper
from nonebot.adapters.onebot.v11 import event as ob11_event
from nonebot.adapters.onebot.v11.event import Reply, Sender
from nonebot.adapters.onebot.v11 import MessageSegment as OB11MS
from nonebot.adapters.red.message import ForwardNode, MediaMessageSegment

from ....webapi import red  # noqa: F401
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

    def construct_media_url(self, bot_self_id: str, seg: MediaMessageSegment) -> str:
        parameters = {
            "botId": bot_self_id,
            "msgId": seg.data["_msg_id"],
            "chatType": seg.data["_chat_type"],
            "target": seg.data["_peer_uin"],
            "elementId": seg.data["id"],
            "thumbSize": 0,
            "downloadType": 2,
        }
        query = urlencode(query=parameters, doseq=True)
        url = urlunsplit(
            (
                "http",
                f"localhost:{self.adapter.driver.config.port}",
                "/ob_pretender/red/media",
                query,
                "",
            )
        )
        return url

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

    def convert_incoming_msg(self, bot: RedBot, incoming: RedMsg) -> OB11Msg:
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
            # elif m.type == "max_member_countrket_face":
            #     msg.append(
            #         OB11MS(
            #             "image",
            #             {
            #                 "file": "file://" + m.data["static_path"],
            #                 "url": "file://" + m.data["static_path"],
            #             },
            #         )
            #     )
            elif m.type == "image" and isinstance(m, MediaMessageSegment):
                msg.append(
                    OB11MS(
                        "image",
                        {
                            "file": "file://" + m.data["path"],
                            "url": self.construct_media_url(bot.self_id, m),
                        },
                    )
                )
            elif m.type == "video" and isinstance(m, MediaMessageSegment):
                msg.append(
                    OB11MS(
                        "video",
                        {
                            "file": "file://" + m.data["path"],
                            "url": self.construct_media_url(bot.self_id, m),
                            "cover": "file://" + m.data["thumb_path"],
                        },
                    )
                )
            elif m.type == "voice" and isinstance(m, MediaMessageSegment):
                msg.append(
                    OB11MS(
                        "record",
                        {
                            "file": "file://" + m.data["path"],
                            "url": self.construct_media_url(bot.self_id, m),
                        },
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
            return await self.send_group_msg(bot, group_id=group_id, message=message)
        elif user_id:
            return await self.send_private_msg(bot, user_id=user_id, message=message)
        elif group_id:
            return await self.send_group_msg(bot, group_id=group_id, message=message)
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
        save_ob11_msg(
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
        save_ob11_msg(
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

    async def _send_forward_msg(
        self,
        bot: RedBot,
        *,
        chat_type: ChatType,
        target: int,
        messages: Union[List[Dict], List[OB11MS], OB11Msg],
    ) -> Dict:
        messages = [
            (
                json.loads(json.dumps(seg, cls=DataclassEncoder))
                if isinstance(seg, OB11MS)
                else seg
            )
            for seg in messages
        ]  # 将Message转换为List

        nodes = []

        for seg in messages:
            if seg.get("type") != "node":
                continue
            data = seg.get("data") or {}

            if "id" in data:
                ob11_msg = await load_ob11_msg(data["id"])
                if ob11_msg is None:
                    continue

                nodes.append(
                    ForwardNode(
                        uin=str(ob11_msg.sender.user_id),
                        name=ob11_msg.sender.nickname,
                        group=ob11_msg.group_id,
                        message=self.convert_outgoing_msg(ob11_msg.message),
                        time=ob11_msg.time,
                    )
                )
            elif "uin" in data or "user_id" in data:
                nodes.append(
                    ForwardNode(
                        uin=str(data.get("uin") or data.get("user_id")),
                        name=data.get("name")
                        or data.get("nickname")
                        or str(data.get("uin") or data.get("user_id")),
                        group=0,
                        message=self.convert_outgoing_msg(
                            OB11Msg(OB11MS(**raw_seg) for raw_seg in data["content"])
                        ),
                    )
                )

        await bot.send_fake_forward(nodes, chat_type, target)
        return {
            "message_id": 0,
            "forward_id": "",
        }

    @api_call_handler()
    async def send_group_forward_msg(
        self, bot: RedBot, *, group_id: int, messages: List[Dict], **data: Dict
    ) -> Dict:
        return await self._send_forward_msg(
            bot, chat_type=ChatType.GROUP, target=group_id, messages=messages
        )

    @api_call_handler()
    async def send_private_forward_msg(
        self, bot: RedBot, *, user_id: int, messages: List[Dict], **data: Dict
    ) -> Dict:
        return await self._send_forward_msg(
            bot, chat_type=ChatType.FRIEND, target=user_id, messages=messages
        )

    @api_call_handler()
    async def get_login_info(self, bot: RedBot, **data: Dict) -> Dict:
        profile = await bot.get_self_profile()
        return {
            "user_id": int(profile.uin or profile.uid or profile.qid),
            "nickname": profile.longNick or profile.nick,
        }

    @api_call_handler()
    async def get_friend_list(self, bot: RedBot, **data: Dict) -> List:
        friends = await bot.get_friends()
        return [
            {
                "user_id": int(profile.uin or profile.uid or profile.qid),
                "nickname": profile.nick,
                "remark": profile.remark,
            }
            for profile in friends
        ]

    @api_call_handler()
    async def get_group_list(self, bot: RedBot, **data: Dict) -> List:
        groups = await bot.get_groups()
        return [
            {
                "group_id": int(group.groupCode),
                "group_name": group.groupName,
                "group_memo": group.remarkName,
                "group_create_time": 0,
                "group_level": 0,
                "member_count": group.memberCount,
                "max_member_count": group.maxMember,
            }
            for group in groups
        ]

    @api_call_handler()
    async def get_group_member_list(
        self, bot: RedBot, *, group_id: int, **data: Dict
    ) -> List:
        members = await bot.get_members(group_id, 2**16 - 1)
        return [
            {
                "group_id": group_id,
                "user_id": int(member.uin or member.uid or member.qid),
                "nickname": member.nick,
                "card": member.cardName,
                "sex": "unknown",
                "age": 0,
                "area": "",
                "join_time": 0,
                "last_sent_time": 0,
                "level": 0,
                "role": "member",  # TODO
                "unfriendly": False,
                "title": "",
                "title_expire_time": 0,
                "card_changeable": False,
                "shut_up_timestamp": member.shutUpTime,
            }
            for member in members
        ]

    @api_call_handler()
    async def delete_msg(self, bot: RedBot, *, message_id: int, **data: Dict) -> None:
        msg = await load_ob11_msg(message_id)
        if msg is None:
            raise ActionFailed(msg="消息不存在")

        if msg.group:
            await bot.recall_group_message(msg.group_id, str(message_id))
        else:
            await bot.recall_friend_message(msg.sender.user_id, str(message_id))

    @api_call_handler()
    async def get_msg(self, bot: RedBot, *, message_id: int, **data: Dict) -> Dict:
        msg = await load_ob11_msg(str(message_id))
        if msg is not None:
            return json.loads(msg.json(exclude_none=True))
        else:
            raise ActionFailed(msg="消息不存在")

    @api_call_handler()
    async def set_group_ban(
        self,
        bot: RedBot,
        *,
        group_id: int,
        user_id: int,
        duration: int = 30 * 60,
        **data: Dict,
    ) -> None:
        if duration > 0:
            await bot.mute_member(group_id, user_id, duration=duration)
        else:
            await bot.unmute_member(group_id, user_id)

    @api_call_handler()
    async def set_group_whole_ban(
        self,
        bot: RedBot,
        *,
        group_id: int,
        enable: bool = True,
        **data: Dict,
    ) -> None:
        if enable:
            await bot.mute_everyone(group_id)
        else:
            await bot.unmute_everyone(group_id)

    @event_handler(red_event.GroupMessageEvent)
    async def handle_group_message_event(
        self, bot: RedBot, event: red_event.GroupMessageEvent
    ) -> ob11_event.GroupMessageEvent:
        msg = self.convert_incoming_msg(bot, event.message)
        ori_msg = self.convert_incoming_msg(bot, event.original_message)

        reply = None
        if event.reply and event.reply.replayMsgId:
            reply = await self.get_msg(bot, message_id=int(event.reply.replayMsgId))
            if reply is not None:
                reply = Reply.parse_obj(reply)

        save_ob11_msg(
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
        msg = self.convert_incoming_msg(bot, event.message)
        ori_msg = self.convert_incoming_msg(bot, event.original_message)

        reply = None
        if event.reply and event.reply.replayMsgId:
            reply = Reply.parse_obj(
                await self.get_msg(bot, message_id=int(event.reply.replayMsgId))
            )

        save_ob11_msg(
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
            sub_type="friend",
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

    @event_handler(red_event.MemberAddEvent)
    async def handle_member_add_event(
        self, bot: RedBot, event: red_event.MemberAddEvent
    ) -> ob11_event.GroupIncreaseNoticeEvent:
        return ob11_event.GroupIncreaseNoticeEvent(
            time=int(event.msgTime or "0"),
            self_id=int(bot.self_id or "0"),
            post_type="notice",
            notice_type="group_increase",
            sub_type="approve",
            user_id=int(event.memberUid or "0"),
            group_id=int(event.peerUin or event.peerUid or "0"),
            operator_id=int(event.operatorUid or "0"),
        )

    @event_handler(red_event.MemberMutedEvent)
    async def handle_member_muted_event(
        self, bot: RedBot, event: red_event.MemberMutedEvent
    ) -> ob11_event.GroupBanNoticeEvent:
        return ob11_event.GroupBanNoticeEvent(
            time=int(datetime.now().timestamp()),
            self_id=int(bot.self_id or "0"),
            post_type="notice",
            notice_type="group_ban",
            sub_type="ban",
            user_id=int(event.member.uin or event.member.uid or "0"),
            group_id=int(event.peerUin or event.peerUid or "0"),
            operator_id=int(event.operator.uin or event.operator.uid or "0"),
            duration=int(event.duration.total_seconds()),
        )

    @event_handler(red_event.MemberUnmuteEvent)
    async def handle_member_unmuted_event(
        self, bot: RedBot, event: red_event.MemberUnmuteEvent
    ) -> ob11_event.GroupBanNoticeEvent:
        return ob11_event.GroupBanNoticeEvent(
            time=int(datetime.now().timestamp()),
            self_id=int(bot.self_id or "0"),
            post_type="notice",
            notice_type="group_ban",
            sub_type="lift_ban",
            user_id=int(event.member.uin or event.member.uid or "0"),
            group_id=int(event.peerUin or event.peerUid or "0"),
            operator_id=int(event.operator.uin or event.operator.uid or "0"),
            duration=int(event.duration.total_seconds()),
        )
