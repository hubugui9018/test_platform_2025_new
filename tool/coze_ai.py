from cozepy import COZE_CN_BASE_URL
from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType, ChatEventType, MessageObjectString


class ImageJudgment:
    def __init__(self):

        coze_api_token = 'pat_WOq9xbQcNTTa6UjdilA1n7VeYAJylfBbI5aQlGV2DgqllhlDGtA0B0Hwe4Qwqz3d'
        coze_api_base = COZE_CN_BASE_URL
        self.coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)
        self.bot_id = '7512361815318249513'
        self.user_id = '123'

    def send_local_image_with_text(self, product_name, remark, pic, assertion_text):
        # 先上传图片到 Coze
        with open(pic, 'rb') as f:
            file_info = self.coze.files.upload(file=f)

        print(f"上传成功，文件ID: {file_info.id}")

        # 创建多模态消息对象 - 使用文件ID
        if assertion_text == '1':
            # print('走到了标准模板')
            print(f'remark:{remark}')
            message_objects = [
                MessageObjectString(type="text",
                                    text=f"先解析收到的图片，然后判断解析的图片与{product_name}知识库，页面字段里的{remark}对应的关键文字字段里的内容和页面内容字段里的内容是否符合。 "
                                         f"如果图片中未显示知识库中所描述的关键文字内容，则直接输出 False； 当图片内容包含知识库中对应页面的关键文字和页面内容，输出True"
                                    ),
                MessageObjectString(type="image", file_id=file_info.id)
            ]

        else:

            message_objects = [
                MessageObjectString(type="text",
                                    text=f"先解析收到的图片，然后{assertion_text} "
                                         f"如果判断不符合我说的，直接输出 False； 如果符合，输出True"),
                MessageObjectString(type="image", file_id=file_info.id)
            ]

        # 使用 build_user_question_objects 方法（流式响应）
        # for event in self.coze.chat.stream(
        #         bot_id=self.bot_id,
        #         user_id=self.user_id,
        #         additional_messages=[
        #             Message.build_user_question_objects(message_objects)
        #         ],
        # ):
        #     if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
        #         return event.message.content
        #
        #     if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
        #         print()
        #         print("token usage:", event.chat.usage.token_count)

        # 使用 stream 方法但收集完整响应
        full_response = ""
        for event in self.coze.chat.stream(
                bot_id=self.bot_id,
                user_id=self.user_id,
                additional_messages=[
                    Message.build_user_question_objects(message_objects)
                ],
        ):
            if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                full_response += event.message.content

            if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
                if hasattr(event.chat, 'usage') and event.chat.usage:
                    print(f"token usage: {event.chat.usage.token_count}")
                break

        return full_response


if __name__ == '__main__':
    product_name = '彩民之家'
    remark = '我的关注'
    pic = r'D:\test_platform_2025_new\587aa52f9eac66bedc884c210b1f438c.jpg'
    assertion_text = 1
    # assertion_text = '判断一下页面有没有红色'

    result = ImageJudgment().send_local_image_with_text(product_name, remark, pic, assertion_text)
    print(result)
