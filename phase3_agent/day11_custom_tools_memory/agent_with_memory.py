"""
agent_with_memory.py — 带记忆系统的 ReAct Agent

功能：
1. MemoryAgent 类 — 集成三级记忆系统的 AI Agent
2. 完整的 ReAct（推理-行动-观察）循环
3. 工具调用 + 记忆检索的融合
4. 多轮对话 + 长期用户偏好记忆

设计原则：
- 零 LangChain 依赖 — 原生 openai SDK 调用
- 记忆与推理分离 — Agent 负责推理，Memory 负责存储
- 每一步可视化 — Thought → Action → Observation
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

from openai import OpenAI  # OpenAI 兼容 SDK
import json  # JSON 序列化
from typing import Optional  # 类型提示

# 导入自定义工具和记忆模块
from tools import get_all_tools, tools_to_openai_format, find_tool
from memory import WorkingMemory, ShortTermMemory, LongTermMemory


# ==================== MemoryAgent 类 ====================

class MemoryAgent:
    """
    带记忆系统的 AI Agent

    核心流程：
    1. 接收用户输入 → 加载相关记忆
    2. 构建上下文（系统提示 + 长期记忆 + 工作记忆 + 对话历史）
    3. LLM 推理 → 决定是否调用工具
    4. 如有工具调用 → 执行工具 → 记录到工作记忆 → 返回步骤 3
    5. 无工具调用 → 生成最终回复 → 更新对话历史 → 提取长期记忆

    记忆层级：
    - WorkingMemory: 当前任务的中间步骤（任务完成后清空）
    - ShortTermMemory: 本次会话的对话历史（滑动窗口）
    - LongTermMemory: 跨会话的用户偏好和重要事实
    """

    def __init__(self, tools: list = None, system_prompt: str = None):
        # 初始化 LLM 客户端
        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

        # 加载工具列表
        self.tools = tools if tools is not None else get_all_tools()

        # 初始化记忆系统
        self.working_memory = WorkingMemory()  # 工作记忆 — 任务级
        self.short_term = ShortTermMemory()    # 短期记忆 — 会话级
        self.long_term = LongTermMemory()      # 长期记忆 — 跨会话

        # 系统提示 — 定义 Agent 的行为准则
        self.system_prompt = system_prompt or (
            "你是一个具有记忆能力的智能助手。你可以使用工具来完成用户的任务。\n\n"
            "## 工作原则\n"
            "1. 分析用户请求，判断是否需要使用工具\n"
            "2. 查阅工作记忆和长期记忆中的相关信息\n"
            "3. 使用工具获取所需信息，将重要中间结果存入工作记忆\n"
            "4. 基于工具返回的结果，给出准确自然的回复\n"
            "5. 记住用户的重要偏好和个人信息\n"
            "6. 如果信息不足，主动询问用户"
        )

        # Agent 配置
        self.max_iterations = 10  # 最大循环次数（安全阀）
        self.verbose = True       # 是否打印详细过程
        self._tool_call_counter = 0  # 工具调用计数器（用于生成唯一 ID）

    def run(self, user_query: str) -> str:
        """运行 Agent 处理用户请求"""
        # 步骤 1：清空工作记忆（每个新任务重新开始）
        self.working_memory.clear()

        # 步骤 2：构建初始消息列表
        messages = self._build_initial_messages(user_query)

        # 步骤 3：ReAct 循环
        openai_tools = tools_to_openai_format(self.tools)

        for iteration in range(1, self.max_iterations + 1):
            if self.verbose:
                print(f"\n{'='*40}")
                print(f"  🔄 Step {iteration}/{self.max_iterations}")
                print(f"{'='*40}")

            # LLM 推理
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=openai_tools,
                tool_choice="auto",
                temperature=0.3
            )

            message = response.choices[0].message

            # 检查是否需要调用工具
            if not message.tool_calls:
                # 无工具调用 → 任务完成
                if self.verbose:
                    print("  💭 Thought: 任务完成，生成最终回复")
                final_reply = message.content or "任务已完成"

                # 更新对话历史
                self.short_term.add_user_message(user_query)
                self.short_term.add_assistant_message(final_reply)

                # 提取长期记忆
                conversation_summary = f"用户: {user_query}\n助手: {final_reply}"
                self.long_term.summarize_and_store(conversation_summary)

                return final_reply

            # 有工具调用 → 执行工具
            messages.append(message)  # 将助手消息加入历史

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                if self.verbose:
                    print(f"  💭 Thought: 我需要使用 {func_name}")
                    print(f"  🎬 Action: {func_name}({json.dumps(func_args, ensure_ascii=False)})")

                # 查找并执行工具
                tool = find_tool(self.tools, func_name)
                if tool is None:
                    result = {"content": [{"type": "text", "text": f"未知工具: {func_name}"}], "isError": True}
                else:
                    try:
                        result = tool.execute(**func_args)
                    except Exception as e:
                        result = {"content": [{"type": "text", "text": f"工具执行失败: {str(e)}"}], "isError": True}

                tool_output = result.get("content", [{}])[0].get("text", "")

                if self.verbose:
                    print(f"  👁️ Observation: {tool_output[:200]}")

                # 记录到工作记忆
                self.working_memory.log_step(f"{func_name}: {json.dumps(func_args, ensure_ascii=False)}", tool_output)

                # 将工具结果添加到消息列表
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output
                })

        # 达到最大循环次数
        return "任务超时：Agent 未能在最大步骤数内完成任务"

    def _build_initial_messages(self, user_query: str) -> list:
        """构建初始消息列表 — 整合系统提示和各层级记忆"""
        messages = []

        # 系统提示 + 长期记忆 + 工作记忆（合并到 system message 中）
        system_content = self.system_prompt

        # 注入长期记忆
        long_term_context = self.long_term.get_all_memories()
        if "暂无长期记忆" not in long_term_context:
            system_content += f"\n\n{long_term_context}\n请在对话中参考以上长期记忆中的用户信息。"

        messages.append({"role": "system", "content": system_content})

        # 注入最近的对话历史
        recent_history = self.short_term.get_recent(10)
        messages.extend(recent_history)

        # 添加当前用户消息
        messages.append({"role": "user", "content": user_query})

        return messages

    def reset_session(self) -> None:
        """重置会话（清空短期记忆和工作记忆，保留长期记忆）"""
        self.short_term.clear()
        self.working_memory.clear()

    def get_memory_report(self) -> str:
        """获取所有记忆状态的报告"""
        lines = ["=" * 40, "  记忆系统报告", "=" * 40]
        lines.append(f"\n工作记忆：{self.working_memory.to_context()}")
        lines.append(f"\n短期记忆：{len(self.short_term)} 条消息")
        lines.append(f"\n长期记忆：\n{self.long_term.get_all_memories()}")
        return "\n".join(lines)


# ==================== 直接测试 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  MemoryAgent 自测")
    print("=" * 60)

    agent = MemoryAgent()
    print(f"✅ Agent 初始化完成，加载了 {len(agent.tools)} 个工具")
    print(f"   工具列表：{', '.join(t.name for t in agent.tools)}")

    # 测试长期记忆
    agent.long_term.remember("test_key", "这是一个测试记忆")
    recalled = agent.long_term.recall("test_key")
    print(f"✅ 长期记忆测试：存储并读取 '{recalled}'")

    # 测试工作记忆
    agent.working_memory.add("temperature", "22°C")
    print(f"✅ 工作记忆测试：{agent.working_memory.get('temperature')}")

    print("\n💡 运行 example.py 查看完整演示")
