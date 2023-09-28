nonebot-adapter-onebot-pretender
======

With some magic ✨

- RedProtocol
  - [x] 消息接收
    - [x] 纯文本
    - [ ] 图片、视频、语音
    - [x] 引用
    - [x] 表情
  - [x] 消息发送
    - [x] 纯文本
    - [x] 图片、视频、语音
    - [x] 引用
    - [x] 表情
  - [ ] 消息发送者角色判断（群主、管理员）
  - [ ] 其他OB11 API

```python
import nonebot
from nonebot import on_command

from nonebot_adapter_onebot_pretender import create_ob11_adapter_pretender, init_onebot_pretender

# init_onebot_pretender 必须在 import adapter 之前

nonebot.init()
init_onebot_pretender()

from nonebot.adapters.red import Adapter as RedAdapter
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, Bot

driver = nonebot.get_driver()

driver.register_adapter(create_ob11_adapter_pretender(RedAdapter))


@on_command("hello").handle()
async def handle_hello(bot: Bot, event: PrivateMessageEvent):
    await bot.send(event, "world")


if __name__ == "__main__":
    nonebot.run()

```
