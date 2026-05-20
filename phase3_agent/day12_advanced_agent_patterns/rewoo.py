"""
rewoo.py — ReWOO 模式的真实 LLM 实现

ReWOO（Reasoning WithOut Observation，无观察推理）模式：
1. LLM 先制定计划，将工具调用嵌入计划中（如 #E1 = search("关键词")）
2. 批量执行所有工具调用（无需等待中间结果）
3. LLM 用实际结果替换占位符，汇总生成最终答案

与 ReAct 的关键区别：
- ReAct: 思考 → 行动 → 观察 → 思考 → 行动 → 观察 ...（串行、多次 LLM 调用）
- ReWOO: 计划中有工具占位符 → 批量执行所有工具 → 一次汇总（并行工具调用、更少 LLM 调用）

适用场景：工具调用之间无依赖关系、需要减少 LLM 调用次数的场景
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

from openai import OpenAI  # OpenAI 兼容 SDK
import json  # JSON 解析
import re  # 正则提取占位符
from tools import get_tools_for_patterns, find_tool_by_name  # 共享工具


class ReWOOAgent:
    """
    ReWOO Agent — 先规划所有工具调用，再批量执行

    核心流程：
    ┌─────────────┐    ┌──────────────┐    ┌────────────┐
    │ 1. 规划阶段   │ → │ 2. 批量执行    │ → │ 3. 汇总阶段  │
    │  Plan + #E   │    │  所有工具调用  │    │ 填充占位符   │
    └─────────────┘    └──────────────┘    └────────────┘
    """

    def __init__(self, tools: list = None, max_steps: int = 10):
        # LLM 客户端
        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        # 工具列表
        self.tools = tools if tools is not None else get_tools_for_patterns()
        # 工具名称映射
        self.tool_map = {t.name: t for t in self.tools}
        # 最大工具调用数
        self.max_steps = max_steps

    def plan(self, task: str) -> tuple:
        """LLM 生成带占位符的计划和工具调用列表"""
        tools_desc = "\n".join([
            f"- {t.name}({list(t.inputSchema.get('properties', {}).keys())}): {t.description[:80]}"
            for t in self.tools
        ])

        planning_prompt = (
            "你是一个任务规划专家。请为以下任务制定执行计划。\n\n"
            f"可用工具：\n{tools_desc}\n\n"
            "规则：\n"
            "1. 分析任务，确定需要哪些工具调用\n"
            "2. 在计划中用占位符 #E1, #E2, #E3... 表示工具调用的结果\n"
            "3. 在每个占位符后面用【】标注工具名称和参数\n"
            "4. 用 JSON 返回，格式：\n"
            '{"plan": "我是计划，#E1 = 搜索结果，#E2 = 计算结果。最终答案基于 #E1 和 #E2。",\n'
            ' "tool_calls": [\n'
            '   {"id": "#E1", "tool": "search", "args": {"query": "关键词"}},\n'
            '   {"id": "#E2", "tool": "calculate", "args": {"expression": "1+2"}}\n'
            ' ]}\n'
        )

        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": planning_prompt},
                {"role": "user", "content": f"任务：{task}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        try:
            plan_data = json.loads(response.choices[0].message.content)
            return plan_data.get("plan", ""), plan_data.get("tool_calls", [])
        except json.JSONDecodeError:
            return task, []

    def execute_batch(self, tool_calls: list) -> dict:
        """批量执行所有工具调用（顺序执行，但不需要 LLM 参与）"""
        results = {}
        for tc in tool_calls:
            tool_name = tc.get("tool", "")
            tool_args = tc.get("args", {})
            placeholder = tc.get("id", "")

            tool = self.tool_map.get(tool_name)
            if tool:
                result = tool.execute(**tool_args)
                text = result.get("content", [{}])[0].get("text", "")
                results[placeholder] = text
                print(f"  🔧 {placeholder}: {tool_name}({json.dumps(tool_args, ensure_ascii=False)})")
                print(f"     → {text[:150]}...")
            else:
                results[placeholder] = f"[错误] 未找到工具: {tool_name}"

        return results

    def synthesize(self, task: str, plan: str,
                   results: dict) -> str:
        """LLM 用实际结果替换占位符后生成最终答案"""
        # 构建结果上下文
        results_text = ""
        for placeholder, text in results.items():
            results_text += f"{placeholder} = {text[:300]}\n\n"

        synthesis_prompt = (
            "你是一个任务总结专家。以下是执行计划中各个占位符的实际结果。"
            "请将占位符替换为实际结果，生成完整、准确的最终答案。\n"
            "不要在答案中保留 #E1 #E2 等占位符，直接引用实际数据。"
        )

        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": synthesis_prompt},
                {"role": "user", "content": (
                    f"原始任务：{task}\n\n"
                    f"执行计划（含占位符）：\n{plan}\n\n"
                    f"占位符的实际结果：\n{results_text}\n\n"
                    f"请生成最终答案。"
                )}
            ],
            temperature=0.5
        )

        return response.choices[0].message.content or "无法生成最终答案"

    def run(self, task: str) -> str:
        """完整的 ReWOO 流程"""
        print(f"\n  📋 任务: {task}")
        print(f"{'─'*50}")

        # 阶段 1：规划 — 生成计划和工具调用列表
        print("  🧠 阶段 1：LLM 制定计划（含工具占位符）...")
        plan, tool_calls = self.plan(task)

        print(f"  📝 计划：\n      {plan[:300]}")
        if tool_calls:
            print(f"  🔧 需要 {len(tool_calls)} 个工具调用：")
            for tc in tool_calls:
                print(f"      {tc.get('id')}: {tc.get('tool')}({json.dumps(tc.get('args', {}), ensure_ascii=False)})")

        # 阶段 2：批量执行所有工具调用
        print(f"\n  ⚙️ 阶段 2：批量执行工具调用...")
        if len(tool_calls) > self.max_steps:
            print(f"  ⚠️ 工具调用数 ({len(tool_calls)}) 超过最大限制 ({self.max_steps})，仅执行前 {self.max_steps} 个")
            tool_calls = tool_calls[:self.max_steps]

        results = self.execute_batch(tool_calls)

        # 阶段 3：汇总 — 填充占位符，生成最终答案
        print(f"\n  📊 阶段 3：LLM 汇总结果...")
        final_answer = self.synthesize(task, plan, results)

        return final_answer


# ==================== 直接测试 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  ReWOO Agent 自测")
    print("=" * 60)

    agent = ReWOOAgent()
    print(f"✅ Agent 初始化完成，{len(agent.tools)} 个工具可用\n")

    # 并行工具调用任务（天气+计算，无依赖关系）
    task = "帮我查一下深度学习的信息，然后计算 25*4+10 的结果"
    print(f"  测试任务: {task}\n")
    try:
        result = agent.run(task)
        print(f"\n{'='*60}")
        print(f"  🎯 最终答案:\n{result}")
    except Exception as e:
        print(f"  ⚠️ LLM 调用失败: {e}")
        print(f"  💡 请确保 .env 中配置了有效的 OPENAI_API_KEY")
