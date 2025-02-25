#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""=================================================
@PROJECT_NAME: agent_example
@File    : model_provider.py
@Author  : Liuyz
@Date    : 2024/6/28 17:12
@Function: 

@Modify History:
         
@Copyright：Copyright(c) 2024-2026. All Rights Reserved
=================================================="""
# import json
# import os


# class ModelProvider(object):
#     def __init__(self):
#         self.api_key = os.environ.get('DASH_SCOPE_API_KEY')
#         self.model_name = os.environ.get('MODEL_NAME')
#         self._client = dashscope.Generation()
#         self.max_retry_time = 3

#     def chat(self, prompt, chat_history):
#         cur_retry_time = 0
#         while cur_retry_time < self.max_retry_time:
#             cur_retry_time += 1
#             try:
#                 messages = [
#                     Message(role="system", content=prompt)
#                 ]
#                 for his in chat_history:
#                     messages.append(Message(role="user", content=his[0]))
#                     messages.append(Message(role="system", content=his[1]))
#                 # 最后1条信息是用户的输入
#                 messages.append(Message(role="user", content=user_prompt))
#                 response = self._client.call(
#                     model=self.model_name,
#                     api_key=self.api_key,
#                     messages=messages
#                 )
#                 # print("response:{}".format(response))
#                 content = json.loads(response["output"]["text"])
#                 return content
#             except Exception as e:
#                 print("call llm exception:{}".format(e))
#         return {}
import json
from openai import OpenAI  # 需要安装openai包
from prompt import user_prompt

class ModelProvider(object):
    def __init__(self):
        OPENAI_API_KEY = "sk-3cdb35e938844a13abee533b7ced659c"
        self.api_key = OPENAI_API_KEY
        self.model = "deepseek-chat"
        self._client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"  # 设置DeepSeek的API端点
        )
        self.max_retry_time = 3

    def chat(self, prompt, chat_history):
        cur_retry_time = 0
        # print(prompt)
        while cur_retry_time < self.max_retry_time:
            cur_retry_time += 1
            try:
                # 构建消息列表
                messages = [
                    {"role": "system", "content": prompt}
                ]
                # 处理历史对话（假设历史记录是用户和模型的交替对话）
                for user_msg, assistant_msg in chat_history:
                    messages.append({"role": "user", "content": user_msg})
                    messages.append({"role": "assistant", "content": assistant_msg})
                # 添加当前用户输入
                messages.append({"role": "user", "content": user_prompt})
                
                # 调用API
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.001,
                    max_tokens=1024,
                    response_format={"type": "json_object"}  # 要求返回JSON格式
                )
                # 解析响应
                content = json.loads(response.choices[0].message.content)
                print(f"响应内容: {content}")
                return content
            except Exception as e:
                print(f"调用模型异常: {e}")
        return {}  # 超过重试次数返回空字典