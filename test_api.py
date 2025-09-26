"""
This example shows how to send image + text input using Coze streaming interface
"""

import os
# Our official coze sdk for Python [cozepy](https://github.com/coze-dev/coze-py)
from cozepy import COZE_CN_BASE_URL

# Get an access_token through personal access token or oauth.
coze_api_token = 'pat_HC0ZGlAqNGa7pPoMcohG18hD8vq4b8xmoSVrPMVUWteXVpeWn23EH86nKI05YJae'
# The default access is api.coze.com, but if you need to access api.coze.cn,
# please use base_url to configure the api endpoint to access
coze_api_base = COZE_CN_BASE_URL

from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType, ChatEventType, MessageObjectString  # noqa

# Init the Coze client through the access_token.
coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

# Create a bot instance in Coze, copy the last number from the web link as the bot's ID.
bot_id = '7512361815318249513'
# The user id identifies the identity of a user. Developers can use a custom business ID
# or a random string.
user_id = '123'

# 方法1: 使用本地图片文件
def send_local_image_with_text():
    # 先上传图片到 Coze
    with open('微信图片_20250605175318.jpg', 'rb') as f:
        file_info = coze.files.upload(file=f)

    print(f"上传成功，文件ID: {file_info.id}")

    # 创建多模态消息对象 - 使用文件ID
    message_objects = [
        MessageObjectString(type="text", text="根据人设与回复逻辑，将图片与知识库对比一下，当图片内容包含知识库中对应页面的关键文字和页面内容，并且还存在额外内容时，判定为符合（即结果为 True），只有关键文字但是没有对应内容，或者没有关键字也没对应内容，输出False"),
        MessageObjectString(type="image", file_id=file_info.id)
    ]

    # 使用 build_user_question_objects 方法
    for event in coze.chat.stream(
        bot_id=bot_id,
        user_id=user_id,
        additional_messages=[
            Message.build_user_question_objects(message_objects)
        ],
    ):
        if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
            print(event.message.content, end="", flush=True)

        if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
            print()
            print("token usage:", event.chat.usage.token_count)

# 方法2: 使用网络图片URL
def send_url_image_with_text():
    image_url = "https://p3-bot-sign.byteimg.com/tos-cn-i-v4nquku3lp/4f9cc67711d74a188f8ca087e5bef16a.png~tplv-v4nquku3lp-image.image?rk3s=68e6b6b5&x-expires=1751782469&x-signature=UfoevxqepM03pxeg7jZFVwnASvo%3D"

    # 创建多模态消息对象
    message_objects = [
        MessageObjectString(type="text", text="根据人设与回复逻辑，将图片与知识库对比一下，当图片内容包含知识库中对应页面的关键文字和页面内容，并且还存在额外内容时，判定为符合（即结果为 True），只有关键文字但是没有对应内容，或者没有关键字也没对应内容，输出False"),
        MessageObjectString(type="image", file_url=image_url)
    ]

    for event in coze.chat.stream(
        bot_id=bot_id,
        user_id=user_id,
        additional_messages=[
            Message.build_user_question_objects(message_objects)
        ],
    ):
        if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
            print(event.message.content, end="", flush=True)

        if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
            print()
            print("token usage:", event.chat.usage.token_count)


# 选择使用哪种方法
if __name__ == "__main__":
    # 使用本地图片文件（推荐）
    send_local_image_with_text()

    # 或者使用网络图片URL
    # send_url_image_with_text()
