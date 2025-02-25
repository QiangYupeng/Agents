# main.py
import os
import json
from model_provider import ModelProvider
from tools import tools_map
from prompt import gen_prompt
from datetime import datetime

import pickle
from pathlib import Path

# # 新增历史文件路径配置
# HISTORY_PATH = Path("/home/qiang/pycharm2022/expycharm/agent/own/data/chat_history.pkl")

# def save_chat_history(history):
#     """保存对话历史到文件"""
#     try:
#         with open(HISTORY_PATH, 'wb') as f:
#             pickle.dump(history, f)
#         print(f"✅ 对话历史已保存至 {HISTORY_PATH}")
#     except Exception as e:
#         print(f"❌ 历史保存失败: {str(e)}")

# def load_chat_history():
#     """从文件加载对话历史"""
#     if not HISTORY_PATH.exists():
#         return []
    
#     try:
#         with open(HISTORY_PATH, 'rb') as f:
#             return pickle.load(f)
#     except (pickle.UnpicklingError, EOFError) as e:
#         print(f"⚠️ 历史文件损坏，已创建新对话: {str(e)}")
#         return []
#     except Exception as e:
#         print(f"❌ 历史加载失败: {str(e)}")
#         return []

# class AgentState:
#     def __init__(self):
#         self.need_human_input = False
#         self.pending_question = ""
#         self.max_retries = 3
#         self.retry_count = 0
        
#     def reset(self):
#         self.need_human_input = False
#         self.pending_question = ""
        
#     def should_retry(self):
#         self.retry_count +=1
#         return self.retry_count < self.max_retries
# def main():
    
#     # 初始化模型
#     state = AgentState()
#     model_provider = ModelProvider()
    
#     # 初始化时加载历史
#     chat_history = load_chat_history()
#     agent_scratch = []

#     if chat_history:
#         print("\n=== 加载历史对话 ===")
#         for i, (query, response) in enumerate(chat_history, 1):
#             print(f"[对话{i}] Q: {query[:30]}...")

#     # 用户输入目标
#     user_query = "查询去新疆的旅游推荐"
#     # input("请输入您的问题或任务目标：")
    
        
#     while True:
#         # 生成提示词（携带完整历史）
#         current_prompt = gen_prompt(user_query, "\n".join(agent_scratch))
        
#         # 处理用户输入需求
#         if state.need_human_input:
#             user_reply = input(f"\n{state.pending_question}\n您的回复：")
#             observation = f"用户答复：{user_reply}"
#             chat_history.append((state.pending_question, observation))
#             state.reset()  # 清除提问状态
        
#         # 调用模型
#         response = model_provider.chat(current_prompt, chat_history)
        
#         try:
#             # 解析响应
#             action_name = response["action"]["name"]
#             args = response["action"]["args"]
#             observation = ""

#             # 处理结束动作
#             if action_name == "finish":
#                 print("\n最终答案：", args["answer"])
#                 break

#             elif action_name == "ask_user":
#                 state.need_human_input = True
#                 state.pending_question = args.get("question", "")
#                 continue  # 跳过后续执行

#             # 执行工具调用
#             elif action_name in tools_map:
#                 import inspect
#                 tool_func = tools_map[action_name]
#                 sig = inspect.signature(tool_func)
#                 required_args = list(sig.parameters.keys())
#                 valid_args = {k:v for k,v in args.items() if k in required_args}
#                 observation = tool_func(**valid_args)
#                 # print(f"\n执行动作: {action_name}({valid_args})")         
#                 print(f"\n执行动作: {action_name}({', '.join(f'{k}={v}' for k, v in valid_args.items())})")
#                 print(f"观察结果: {observation}")
#             else:
#                 observation = f"错误：未知动作 {action_name}"
#                 print(observation)

#             # 更新对话历史
#             chat_history.append((user_query, json.dumps(response, ensure_ascii=False)))
#             agent_scratch.append(f"{response['thoughts']['speak']} -> {observation}")
    
         

#         except (KeyError, json.JSONDecodeError) as e:
#             print(f"响应解析错误: {str(e)}")
#             break
#         except Exception as e:
#             print(f"执行异常: {str(e)}")
#             break

# if __name__ == "__main__":
#     # 设置环境变量（示例值，实际使用请替换）
#     os.environ['WORKDIR_ROOT'] = './llm_result'  # 文件操作目录
#     os.environ['TAVILY_API_KEY'] = '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'
#     # 创建工作目录
#     if not os.path.exists(os.environ['WORKDIR_ROOT']):
#         os.makedirs(os.environ['WORKDIR_ROOT'])
#     start_time = datetime.now()
#     main()
#     print(f"耗时: {(datetime.now()-start_time).total_seconds()}秒")


# -*- coding: utf-8 -*-
import os
import json
import time
import pickle
from pathlib import Path
from functools import wraps
from datetime import datetime
import inspect

# ================== 配置部分 ==================
MAX_HISTORY = 20  # 最多保留20轮对话
HISTORY_DIR = Path("./histories")  # 历史存储目录

# ================== 装饰器 ==================
def timeit(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"⏱️ {func.__name__} 耗时: {time.time()-start:.2f}s")
        return result
    return wrapper

# ================== 持久化模块 ==================
class HistoryManager:
    def __init__(self, user_id="default"):
        self.user_id = user_id
        HISTORY_DIR.mkdir(exist_ok=True)
        self.history_path = HISTORY_DIR / f"{user_id}.pkl"
        
    def save(self, history):
        """保存对话历史"""
        try:
            # 保留最近N条记录
            trimmed = history[-MAX_HISTORY:]
            with open(self.history_path, 'wb') as f:
                pickle.dump(trimmed, f)
            print(f"✅ 对话历史已保存至 {self.history_path}")
        except Exception as e:
            print(f"❌ 历史保存失败: {str(e)}")

    def load(self):
        """加载对话历史"""
        if not self.history_path.exists():
            return []
        try:
            with open(self.history_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"⚠️ 历史加载失败: {str(e)}")
            return []

# ================== 输入验证 ==================
def validate_input(func):
    """输入验证装饰器"""
    @wraps(func)
    def wrapper(question):
        while True:
            reply = func(question)
            if len(reply.strip()) >= 2:
                return reply
            print("❌ 输入无效，至少需要2个字符")
    return wrapper

# ================== 工具函数增强 ==================
@validate_input
def ask_user(question):
    """带输入验证的询问函数"""
    print(f"\n[系统需要补充信息] {question}")
    return input("您的回复（输入/history查看对话记录）：")

# ================== 主程序增强 ==================
class AgentCore:
    def __init__(self, user_id):
        self.history_mgr = HistoryManager(user_id)
        self.chat_history = self.history_mgr.load()
        self.agent_scratch = []
        self.state = {
            'need_input': False,
            'pending_question': None,
            'start_time': datetime.now()
        }

    def show_history(self):
        """显示对话历史"""
        print("\n=== 最近对话记录 ===")
        for idx, (q, r) in enumerate(self.chat_history[-5:], 1):
            print(f"{idx}. Q: {q[:40]}...\n   R: {r[:60]}...")

    def process_command(self, input_str):
        """处理特殊命令"""
        if input_str == '/history':
            self.show_history()
            return True
        return False

    @timeit
    def execute_tool(self, action_name, args):
        """执行工具调用"""
        tool_func = tools_map[action_name]
        sig = inspect.signature(tool_func)
        valid_args = {k:v for k,v in args.items() if k in sig.parameters}
        return tool_func(**valid_args)

def main():
    # 初始化用户系统
    user_id = input("请输入您的用户ID：").strip() or "anonymous"
    agent = AgentCore(user_id)
    model_provider = ModelProvider()  # 需提前实现
    
    # 显示系统信息
    print(f"\n🕒 会话开始时间: {agent.state['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📚 加载到{len(agent.chat_history)}条历史记录")

    # 主循环
    while True:
        try:
            # 处理用户输入阶段
            if agent.state['need_input']:
                user_reply = ask_user(agent.state['pending_question'])
                
                # 处理特殊命令
                if agent.process_command(user_reply):
                    continue
                    
                observation = f"用户答复：{user_reply}"
                agent.chat_history.append((agent.state['pending_question'], observation))
                agent.state['need_input'] = False

            # 生成提示词
            current_prompt = gen_prompt(
                query=agent.chat_history[-1][0] if agent.chat_history else "",
                agent_scratch="\n".join(agent.agent_scratch)
            )

            # 调用模型
            response = model_provider.chat(current_prompt, agent.chat_history)
            
            # 处理响应
            action_name = response["action"]["name"]
            args = response["action"]["args"]

            if action_name == "finish":
                print(f"\n🏁 最终答案：{args['answer']}")
                agent.history_mgr.save(agent.chat_history)
                break

            elif action_name == "ask_user":
                agent.state.update({
                    'need_input': True,
                    'pending_question': args.get("question", "")
                })
                continue

            elif action_name in tools_map:
                observation = agent.execute_tool(action_name, args)
                print(f"\n🔧 执行动作: {action_name}({args})")
                print(f"📌 观察结果: {observation[:100]}...")

                # 更新状态
                agent.chat_history.append((json.dumps(response), observation))
                agent.agent_scratch.append(f"{response['thoughts']['speak']} -> {observation}")

            agent.history_mgr.save(agent.chat_history)

        except Exception as e:
            print(f"\n⚠️ 系统异常: {str(e)}")
            agent.history_mgr.save(agent.chat_history)
            break

if __name__ == "__main__":
    # 创建必要目录
    HISTORY_DIR.mkdir(exist_ok=True)
    os.environ['TAVILY_API_KEY'] = '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'
    
    start_time = datetime.now()
    main()
    print(f"耗时: {(datetime.now()-start_time).total_seconds()}秒")