import json

import nonebot
from nonebot import on_command

nonebot.init()

# init_onebot_pretender 必须在 import adapter 之前

from nonebot_adapter_onebot_pretender import (
    init_onebot_pretender,
    create_ob11_adapter_pretender,
)

init_onebot_pretender()

from nonebot.adapters.red import Adapter as RedAdapter
from nonebot.adapters.onebot.v11 import Bot, MessageEvent

driver = nonebot.get_driver()

driver.register_adapter(create_ob11_adapter_pretender(RedAdapter))

nonebot.load_from_toml("pyproject.toml")


@on_command("hello").handle()
async def handle_hello(bot: Bot, event: MessageEvent):
    await bot.send(event, "world")


@on_command("get_group_list").handle()
async def handle(bot: Bot, event: MessageEvent):
    res = await bot.get_group_list()
    await bot.send(event, json.dumps(res))


if __name__ == "__main__":
    nonebot.run()
