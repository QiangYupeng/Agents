# -*- coding: utf-8 -*-
import os
import json
import time
import pickle
import inspect
from pathlib import Path
from functools import wraps
from datetime import datetime
from model_provider import ModelProvider
from tools import tools_map
from prompt import gen_prompt

# ================== 全局配置 ==================
MAX_HISTORY = 20  # 最大历史记录数
HISTORY_DIR = Path("./histories")  # 历史存储目录


# ================== 装饰器 ==================
def timeit(func):
    """执行耗时监控"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"⏱️ {func.__name__} 耗时: {time.time() - start:.2f}s")
        return result

    return wrapper


# ================== 持久化模块 ==================
class HistoryManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.file_path = HISTORY_DIR / f"{user_id}.pkl"
        HISTORY_DIR.mkdir(exist_ok=True)

    def save(self, new_records):
        """智能保存历史记录"""
        try:
            # 合并新旧记录并截断
            existing = self.load()['records']
            merged = existing + new_records
            data = {
                'meta': {
                    'version': 1.2,
                    'saved_at': datetime.now().isoformat(),
                    'user': self.user_id
                },
                'records': merged[-MAX_HISTORY:]
            }
            with open(self.file_path, 'wb') as f:
                pickle.dump(data, f)
            print(f"✅ 已保存{len(data['records'])}条历史记录")
        except Exception as e:
            print(f"❌ 保存失败: {str(e)}")

    def load(self):
        """安全加载历史记录"""
        if not self.file_path.exists():
            return {'meta': None, 'records': []}

        try:
            with open(self.file_path, 'rb') as f:
                data = pickle.load(f)

                # 兼容旧版列表格式
                if isinstance(data, list):  # 旧版数据格式
                    return {
                        'meta': {'version': '1.0-legacy'},
                        'records': data
                    }
                # 新版字典格式
                return {
                    'meta': data.get('meta', {}),
                    'records': data.get('records', [])
                }
        except Exception as e:
            print(f"⚠️ 历史加载异常: {str(e)}")
            return {'meta': None, 'records': []}


# ================== 输入验证 ==================
def validate_input(func):
    """输入有效性验证"""

    @wraps(func)
    def wrapper(question):
        while True:
            reply = func(question)
            if len(reply.strip()) >= 2:
                return reply
            print("❌ 输入无效，至少需要2个字符")

    return wrapper


# ================== 核心逻辑 ==================
class AgentCore:
    def __init__(self, user_id):
        self.history_mgr = HistoryManager(user_id)
        self._init_state()

    def _init_state(self):
        """初始化运行时状态"""
        self.agent_scratch = []
        self.chat_history = self.history_mgr.load()['records']
        self.state = {
            'need_input': False,
            'pending_question': None,
            'start_time': datetime.now()
        }

    def show_history(self, count=5):
        """显示最近的对话历史"""
        print("\n=== 最近对话记录 ===")
        for idx, (q, r) in enumerate(self.chat_history[-count:], 1):
            print(f"{idx}. [{q[:20]}...] -> {r[:30]}...")

    def process_command(self, cmd):
        """处理特殊命令"""
        if cmd == '/history':
            self.show_history()
            return True
        elif cmd == '/clear':
            self.chat_history = []
            print("🗑️ 已清除对话历史")
            return True
        return False

    @timeit
    def execute_tool(self, action_name, args):
        """执行工具调用"""
        tool_func = tools_map.get(action_name)
        if not tool_func:
            raise ValueError(f"未知工具: {action_name}")

        sig = inspect.signature(tool_func)
        valid_args = {
            k: v for k, v in args.items()
            if k in sig.parameters
        }
        return tool_func(**valid_args)


# ================== 主程序 ==================
@validate_input
def get_user_input(prompt):
    """获取用户输入"""
    return input(prompt)


def main_loop(model_provider):
    """主交互循环"""
    print("\n" + "=" * 40)
    print("🚀 智能助手系统已启动")
    print("🔍 可用命令：/history, /clear, exit")
    print("=" * 40)

    user_id = get_user_input("🔑 请输入用户ID：")
    agent = AgentCore(user_id)
    # 显示系统信息
    print(f"\n🕒 会话开始时间: {agent.state['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print("agent.chat_history: ", agent.chat_history)
    print(f"📚 加载到{len(agent.chat_history)}条历史记录")

    while True:
        try:
            # 获取新查询
            current_query = get_user_input("\n📢 请输入问题（输入exit退出）：")
            if current_query.lower() == 'exit':
                print("👋 感谢使用，再见！")
                break
            if agent.process_command(current_query):
                continue

            # 处理单次查询
            agent._init_state()  # 重置运行时状态
            while True:
                # 处理用户追问
                if agent.state['need_input']:
                    reply = get_user_input(f"\n❓ {agent.state['pending_question']}\n💬 您的回复：")
                    if agent.process_command(reply):
                        continue

                    agent.chat_history.append((
                        agent.state['pending_question'],
                        f"用户答复：{reply}"
                    ))
                    agent.state['need_input'] = False

                # 生成提示
                prompt = gen_prompt(
                    query=current_query,
                    agent_scratch="\n".join(agent.agent_scratch)
                )

                # print(prompt)

                # 调用模型
                response = model_provider.chat(current_query, prompt, agent.chat_history)

                # 解析响应
                action = response["action"]
                action_name = action["name"]
                args = action["args"]

                # 终止动作
                if action_name == "finish":
                    print(f"\n🏁 最终答案：{args['answer']}")
                    agent.history_mgr.save(agent.chat_history)
                    break

                # 用户追问
                if action_name == "ask_user":
                    agent.state.update({
                        'need_input': True,
                        'pending_question': args.get("question")
                    })
                    continue

                # 工具调用
                if action_name in tools_map:
                    observation = agent.execute_tool(action_name, args)
                    print(f"\n🔧 执行: {action_name}({args})")
                    print(f"📋 结果: {str(observation)[:100]}...")

                    # 更新状态
                    agent.chat_history.append((
                        json.dumps(response, ensure_ascii=False),
                        observation
                    ))
                    agent.agent_scratch.append(
                        f"{response['thoughts']['speak']} -> {observation}"
                    )

                agent.history_mgr.save(agent.chat_history)

        except KeyboardInterrupt:
            print("\n⚠️ 用户中断操作")
            agent.history_mgr.save(agent.chat_history)
            break
        except Exception as e:
            print(f"\n❌ 系统错误: {str(e)}")
            agent.history_mgr.save(agent.chat_history)


if __name__ == "__main__":
    # 初始化环境
    os.environ['TAVILY_API_KEY'] = 'Your-key'  # 替换实际API密钥
    HISTORY_DIR.mkdir(exist_ok=True)

    # 启动系统
    main_loop(ModelProvider())  # 需实现ModelProvider类
