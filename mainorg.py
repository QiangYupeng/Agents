# main.py
import os
import json
from model_provider import ModelProvider
from tools import tools_map
from prompt import gen_prompt

# import json
# import os
# from prompt import user_prompt

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


def main():
    # 初始化模型
    model_provider = ModelProvider()
    
    # 初始化对话历史
    chat_history = []
    agent_scratch = []
    
    # 用户输入目标
    user_query = input("请输入您的问题或任务目标：")
    
    while True:
        # 生成提示词
        current_prompt = gen_prompt(user_query, "\n".join(agent_scratch))
        
        # 调用模型
        response = model_provider.chat(current_prompt, chat_history)
        
        try:
            # 解析响应
            action_name = response["action"]["name"]
            args = response["action"]["args"]
            observation = ""

            # 处理结束动作
            if action_name == "finish":
                print("\n最终答案：", args["answer"])
                break
 
            # 执行工具调用
            if action_name in tools_map:
                tool_func = tools_map[action_name]
                # 参数验证
                required_args = list(tool_func.__annotations__.keys() if hasattr(tool_func, '__annotations__') else [])
                actual_args = {k: v for k, v in args.items() if k in required_args}
                
                # 执行工具
                observation = tool_func(**actual_args)
                print(f"\n执行动作: {action_name}({', '.join(f'{k}={v}' for k, v in actual_args.items())})")
                print(f"观察结果: {observation}")
            else:
                observation = f"错误：未知动作 {action_name}"
                print(observation)

            # 更新对话历史
            chat_history.append((user_query, json.dumps(response, ensure_ascii=False)))
            agent_scratch.append(f"{response['thoughts']['speak']} -> {observation}")

        except (KeyError, json.JSONDecodeError) as e:
            print(f"响应解析错误: {str(e)}")
            break
        except Exception as e:
            print(f"执行异常: {str(e)}")
            break

if __name__ == "__main__":
    # 创建必要目录  去掉ask_user函数
    # HISTORY_DIR.mkdir(exist_ok=True)
    os.environ['TAVILY_API_KEY'] = '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'

    main()