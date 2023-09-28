from asyncio import create_task
from typing import List, Literal, Optional

from nonebot import logger
from pydantic import Field, BaseModel
from nonebot.adapters.onebot.v11 import Message
from nonebot.adapters.onebot.v11.event import Sender
from nonebot.utils import DataclassEncoder, run_sync

from nonebot_adapter_onebot_pretender.data import db


class OB11MsgModel(BaseModel):
    message_id: int
    group: bool = False
    group_id: Optional[int]
    real_id: int = 0
    message_type: Literal["group", "private"]
    sender: Sender = Field(default_factory=Sender)
    time: int = 0
    message: Message = Field(default_factory=Message)
    raw_message: str = ""
    forward: Optional[List[dict]]

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


def save_ob11_msg(message_id: str, message: OB11MsgModel):
    create_task(_do_save_ob11_msg(message_id, message))
