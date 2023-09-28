from typing import cast

from fastapi import Response
from starlette import status
from nonebot import get_app, get_bot
from starlette.responses import StreamingResponse
from nonebot.adapters.red.api.model import ChatType
from nonebot.adapters.red import Adapter as RedAdapter

from ..v11.adapter import Adapter as OB11PretenderAdapter

app = get_app()


@app.get("/ob_pretender/red/media")
async def get_red_media(
    response: Response,
    botId: str,
    msgId: str,
    chatType: ChatType,
    target: str,
    elementId: str,
    thumbSize: int = 0,
    downloadType: int = 2,
):
    bot = get_bot(botId)
    if bot is None or not isinstance(bot.adapter, OB11PretenderAdapter):
        response.status_code = status.HTTP_404_NOT_FOUND
        return

    bot = cast(OB11PretenderAdapter, bot.adapter).get_actual_bot(bot)
    if bot.type != RedAdapter.get_name():
        response.status_code = status.HTTP_404_NOT_FOUND
        return

    async def fetch():
        yield await bot.call_api(
            "fetch_media",
            msg_id=msgId,
            chat_type=chatType,
            target=target,
            element_id=elementId,
            thumb_size=thumbSize,
            download_type=downloadType,
        )

    return StreamingResponse(fetch())
