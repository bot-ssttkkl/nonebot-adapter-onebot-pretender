nonebot-adapter-onebot-pretender
======

With some magic ✨

- RedProtocol
  - [x] 消息接收
    - [x] 纯文本
    - [x] 图片、视频、语音
    - [x] 引用
    - [x] 表情
  - [x] 消息发送
    - [x] 纯文本
    - [x] 图片、视频、语音
    - [x] 引用
    - [x] 表情
    - [ ] 合并转发（调不通orz）
  - [ ] 消息发送者角色判断（消息上报少字段orz）
  - [ ] 其他OB11事件
    - [ ] 群名称改动事件
    - [ ] 群成员禁言/解除禁言事件
    - [ ] 群成员加入事件 (包括旧版受邀请入群)
  - [ ] 其他OB11 API
    - [x] 获取自身资料get_login_info
    - [x] 获取好友、群组get_friend_list/get_group_list
    - [ ] 获取群组内群员资料get_group_member_list（调不通orz [https://github.com/chrononeko/bugtracker/issues/12]）
    - [ ] 获取群公告
    - [ ] 禁言/解禁群员
    - [ ] 全体禁言
    - [ ] 获取历史消息

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
