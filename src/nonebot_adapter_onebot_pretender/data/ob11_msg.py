from typing import Optional
from asyncio import create_task

from nonebot import logger
from pydantic import BaseModel
from nonebot.adapters.onebot.v11 import Message
from nonebot.adapters.onebot.v11.event import Sender
from nonebot.utils import DataclassEncoder, run_sync

from nonebot_adapter_onebot_pretender.data import db


class OB11MsgModel(BaseModel):
    group: bool
    group_id: Optional[int]
    message_id: int
    real_id: int
    message_type: str
    sender: Sender
    time: int
    message: Message
    raw_message: str

    class Config:
        extra = "allow"
        json_encoders = {Message: DataclassEncoder}


@run_sync
def load_ob11_msg(message_id: str) -> Optional[OB11MsgModel]:
    try:
        msg = db[f"ob11_msg_{message_id}"]
        msg = OB11MsgModel.parse_raw(msg, content_type="json")
        return msg
    except KeyError:
        return None


@run_sync
@logger.catch
def _do_save_ob11_msg(message_id: str, message: OB11MsgModel):
    db[f"ob11_msg_{message_id}"] = message.json()
    logger.debug(f"Saved OB11 Msg: {message.dict()}")


async def save_ob11_msg(message_id: str, message: OB11MsgModel):
    create_task(_do_save_ob11_msg(message_id, message))
