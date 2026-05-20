"""
agent_basics.py
从零实现ReAct Agent — 不使用任何框架，纯原生openai SDK

功能：
1. ReActAgent类：完整的ReAct(推理-行动-观察)循环
2. 工具系统：可注册/移除/发现工具
3. 思考过程可视化：每一步打印Thought→Action→Observation
4. 停止条件：无工具调用/最大步骤/用户确认
5. 实战：天气查询 + 计算 + 待办事项管理

学习目标：
1. 理解Agent底层的完整运行机制
2. 掌握Tool Calling Loop的生产级实现
3. 能独立构建和扩展Agent系统
4. 为Day10的MCP协议集成打下基础
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from openai import OpenAI
import json
import math
from datetime import datetime
from typing import Dict, List, Callable, Optional, Any

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


# ==================== 工具函数定义 ====================

def get_weather(city: str) -> dict:
    """获取指定城市的天气信息"""
    weather_db = {
        "北京": {"temperature": 20, "condition": "晴", "humidity": 45},
        "上海": {"temperature": 25, "condition": "多云", "humidity": 60},
        "广州": {"temperature": 30, "condition": "小雨", "humidity": 75},
        "深圳": {"temperature": 28, "condition": "阴", "humidity": 70},
        "杭州": {"temperature": 22, "condition": "晴转多云", "humidity": 55},
    }
    if city in weather_db:
        return {"success": True, "city": city, "data": weather_db[city]}
    return {"success": False, "city": city, "message": f"未找到{city}的天气信息"}


def calculate(expression: str) -> dict:
    """安全的数学计算"""
    try:
        allowed = set("0123456789.+-*/()% eEpPiI")
        if not all(c in allowed for c in expression):
            return {"success": False, "message": "表达式包含不支持的字符"}
        result = eval(expression, {"__builtins__": {}},
                      {"e": 2.718, "pi": 3.1416, "E": 2.718, "PI": 3.1416})
        return {"success": True, "expression": expression, "result": result}
    except Exception as e:
        return {"success": False, "expression": expression, "message": str(e)}


# 待办事项存储（模拟数据库）
_todo_list: List[Dict] = []


def todo_add(task: str, priority: str = "medium") -> dict:
    """添加待办事项"""
    _todo_list.append({
        "id": len(_todo_list) + 1,
        "task": task,
        "priority": priority,
        "done": False,
        "created_at": datetime.now().isoformat()
    })
    return {"success": True, "total": len(_todo_list), "task": task}


def todo_list() -> dict:
    """列出所有待办事项"""
    return {"success": True, "items": _todo_list, "total": len(_todo_list)}


def todo_done(task_id: int) -> dict:
    """标记待办事项为完成"""
    for item in _todo_list:
        if item["id"] == task_id:
            item["done"] = True
            return {"success": True, "completed": item["task"]}
    return {"success": False, "message": f"未找到ID为{task_id}的待办事项"}


# ==================== ReActAgent 类 ====================

class ReActAgent:
    """
    ReAct (Reasoning + Acting) Agent

    核心流程:
    1. 接收用户任务
    2. LLM推理 → 决定是否需要调用工具
    3. 如果需要工具 → 执行工具 → 将结果返回LLM
    4. 重复步骤2-3，直到LLM给出最终回复
    """

    def __init__(self, system_prompt: str = None):
        """
        初始化Agent

        参数:
            system_prompt: 系统提示词，定义Agent的角色和行为
        """
        self.system_prompt = system_prompt or """你是一个智能Agent助手。你可以使用提供的工具来完成用户的任务。

## 工作原则
1. 分析用户请求，判断需要哪些信息
2. 使用工具获取所需信息
3. 基于工具返回的结果，给出准确回复
4. 如果工具调用失败，尝试其他方法
5. 如果信息不足，明确告知用户"""

        # 工具注册表: {name: {"schema": ..., "function": ...}}
        self.tools_registry: Dict[str, Dict] = {}
        # 默认的最大循环次数
        self.max_iterations = 10
        # 是否打印详细的思考过程
        self.verbose = True
        # 是否需要用户确认才能执行某些操作
        self.confirmation_required = False

    def register_tool(self, name: str, description: str,
                      parameters: dict, func: Callable) -> None:
        """
        注册一个工具到Agent

        参数:
            name: 工具名称（LLM会看到的名称）
            description: 工具描述（决定LLM何时调用）
            parameters: JSON Schema格式的参数定义
            func: 实际执行的Python函数
        """
        self.tools_registry[name] = {
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            },
            "function": func
        }

    def _build_tools_list(self) -> list:
        """构建发给LLM的tools列表"""
        return [info["schema"] for info in self.tools_registry.values()]

    def _execute_tool(self, name: str, arguments: dict) -> str:
        """
        执行工具并返回结果的JSON字符串

        参数:
            name: 工具名称
            arguments: 工具参数（已解析为dict）

        返回:
            工具执行结果的JSON字符串
        """
        if name not in self.tools_registry:
            return json.dumps({"success": False, "message": f"未知工具: {name}"},
                              ensure_ascii=False)
        try:
            func = self.tools_registry[name]["function"]
            result = func(**arguments)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "message": str(e)}, ensure_ascii=False)

    def run(self, user_query: str) -> str:
        """
        运行Agent处理用户请求

        参数:
            user_query: 用户输入

        返回:
            Agent的最终回复文本
        """
        # 初始化消息列表
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_query}
        ]

        tools = self._build_tools_list()

        for iteration in range(1, self.max_iterations + 1):
            if self.verbose:
                print(f"\n{'='*40}")
                print(f"🔄 Step {iteration}/{self.max_iterations}")
                print(f"{'='*40}")

            # 步骤1: LLM思考
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=tools if tools else None,  # 没有工具时不传tools
                tool_choice="auto" if tools else None
            )

            message = response.choices[0].message

            # 步骤2: 检查是否需要调用工具
            if not message.tool_calls:
                # 没有工具调用 → Agent完成了任务
                if self.verbose:
                    print("💭 Thought: 任务完成，无需更多工具调用")
                return message.content or "任务已完成"

            # 步骤3: 有工具调用 → 执行工具
            # 将LLM的回复添加到历史中
            messages.append(message)

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                # 打印思考过程
                if self.verbose:
                    print(f"💭 Thought: 我需要使用 {func_name}")
                    print(f"🎬 Action: {func_name}({json.dumps(func_args, ensure_ascii=False)})")

                # 用户确认模式
                if self.confirmation_required:
                    confirm = input(f"\n⚠️ Agent要调用 {func_name}，允许吗？(y/n): ")
                    if confirm.lower() != 'y':
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps({"success": False, "message": "用户拒绝执行"},
                                                  ensure_ascii=False)
                        })
                        continue

                # 执行工具
                result = self._execute_tool(func_name, func_args)

                if self.verbose:
                    print(f"👁️ Observation: {result}")

                # 将工具结果添加到历史
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

        # 达到最大迭代次数
        return "任务超时：Agent未能在最大步骤数内完成任务"


# ==================== 演示函数 ====================

def demo_simple_agent():
    """演示基础Agent"""
    print("=" * 60)
    print("📋 1. 基础Agent — 单一工具调用")
    print("-" * 60)

    agent = ReActAgent()
    # 注册一个工具
    agent.register_tool(
        name="get_weather",
        description="获取指定城市的当前天气信息",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"}
            },
            "required": ["city"]
        },
        func=get_weather
    )

    queries = [
        "北京天气怎么样？",
        "不用查工具，直接回复：你好世界",
    ]
    for q in queries:
        print(f"\n👤 用户: {q}")
        answer = agent.run(q)
        print(f"🤖 Agent: {answer}")


def demo_multi_tool_agent():
    """演示多工具Agent"""
    print("\n" + "=" * 60)
    print("📋 2. 多工具Agent — 天气 + 计算 + 待办")
    print("-" * 60)

    agent = ReActAgent()
    agent.register_tool("get_weather", "获取指定城市的天气信息", {
        "type": "object",
        "properties": {"city": {"type": "string", "description": "城市名称"}},
        "required": ["city"]
    }, get_weather)

    agent.register_tool("calculate", "执行数学计算", {
        "type": "object",
        "properties": {"expression": {"type": "string", "description": "数学表达式"}},
        "required": ["expression"]
    }, calculate)

    agent.register_tool("todo_add", "添加待办事项", {
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "任务描述"},
            "priority": {"type": "string", "description": "优先级: low/medium/high"}
        },
        "required": ["task"]
    }, todo_add)

    agent.register_tool("todo_list", "列出所有待办事项", {
        "type": "object", "properties": {}, "required": []
    }, todo_list)

    # 复杂任务：需要多步推理
    query = """帮我完成以下任务：
1. 查一下杭州天气
2. 把杭州的温度乘以2算一下是多少
3. 如果结果大于40，帮我添加一个待办事项"杭州温度警告"
"""
    print(f"\n👤 用户: {query}")
    answer = agent.run(query)
    print(f"\n🤖 Agent 最终回复: {answer}")
    print(f"\n📋 当前待办事项: {todo_list()}")


def demo_agent_with_trace():
    """演示带思考过程追踪的Agent"""
    print("\n" + "=" * 60)
    print("📋 3. Agent思考过程可视化")
    print("-" * 60)
    print("（verbose=True时自动输出每一步的思考过程）")
    # 以上面的multi-tool agent为例，verbose已开启


def main():
    """主函数"""
    print("=" * 60)
    print("Day 09: Agent基础 — 从零实现ReAct Agent")
    print("=" * 60)
    print("🔧 零框架依赖，纯原生openai SDK实现")
    print("=" * 60)

    try:
        demo_simple_agent()
        demo_multi_tool_agent()

        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        print("=" * 60)
        print("\n💡 ReActAgent类的关键设计:")
        print("  1. register_tool() — 注册工具（名称+描述+Schema+函数）")
        print("  2. run() — Tool Calling Loop循环直到完成")
        print("  3. verbose — 可视化每一步的Thought→Action→Observation")
        print("  4. max_iterations — 安全阀，防止无限循环")
        print("\n⚠️ 注意：这里没有任何LangChain/LangGraph依赖！")
        print("   明天将学习用MCP协议标准化工具暴露")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()