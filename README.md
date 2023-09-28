# nonebot-adapter-onebot-pretender

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
    - [x] 群成员禁言/解除禁言事件
    - [x] 群成员加入事件 (包括旧版受邀请入群)
    - [ ] 群名称改动事件
  - [ ] 其他OB11 API
    - [x] 获取自身资料get_login_info
    - [x] 获取好友、群组get_friend_list/get_group_list
    - [x] 消息撤回
    - [ ] 获取群组内群员资料get_group_member_list（调不通orz [https://github.com/chrononeko/bugtracker/issues/12]）
    - [x] 禁言/解禁群员
    - [x] 全体禁言
    - [ ] 获取群公告
    - [ ] 获取历史消息

# 测试过的版本

- nonebot2 2.1.0
- nonebot-adapter-onebot 2.3.0
- nonebot-adapter-red 0.5.1

由于本项目的特殊性，不保证在其他版本的nonebot/red适配器中也能工作。

# DEMO

1、创建一个bot.py

2、写入下列内容

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

3、开润
