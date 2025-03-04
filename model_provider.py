#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import json
from openai import OpenAI 
from prompt import generate_user_prompt

class ModelProvider(object):
    def __init__(self):
        OPENAI_API_KEY = "Your-API-KEY"
        self.api_key = OPENAI_API_KEY
        self.model = "deepseek-chat"
        self._client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"  # 设置DeepSeek的API端点
        )
        self.max_retry_time = 3

    def chat(self, current_query, current_prompt, chat_history):
        cur_retry_time = 0
        # print(prompt)
        while cur_retry_time < self.max_retry_time:
            cur_retry_time += 1
            try:
                # 构建消息列表
                messages = [{"role": "system", "content": current_prompt}]
                # 处理历史对话（假设历史记录是用户和模型的交替对话）
                for user_msg, assistant_msg in chat_history:
                    messages.append({"role": "user", "content": user_msg})
                    messages.append({"role": "assistant", "content": assistant_msg})
                # 添加当前用户输入
                messages.append({"role": "user", "content": generate_user_prompt(current_query)})
                
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
