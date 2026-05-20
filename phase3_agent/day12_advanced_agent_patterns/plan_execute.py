"""
plan_execute.py — Plan-Execute 模式的真实 LLM 实现

Plan-Execute（计划-执行）模式：
1. LLM 分析任务 → 生成详细的执行计划（多个步骤）
2. 按顺序逐步执行每个计划步骤
3. 在每一步中，LLM 决定是否需要调用工具
4. 所有步骤完成后，LLM 汇总结果生成最终答案

适用场景：复杂的多步骤任务，如调研报告、项目规划、数据分析
特点：可解释性强，用户能看到完整的执行计划
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

from openai import OpenAI  # OpenAI 兼容 SDK
import json  # JSON 解析
from tools import get_tools_for_patterns, find_tool_by_name  # 共享工具


class PlanExecuteAgent:
    """
    Plan-Execute Agent

    核心流程：
    ┌──────────┐    ┌──────────────┐    ┌──────────┐
    │ 1. 制定计划 │ → │ 2. 逐步执行    │ → │ 3. 汇总结果 │
    │  (Planning) │    │ (Execution)   │    │ (Synthesis)│
    └──────────┘    └──────────────┘    └──────────┘
    """

    def __init__(self, tools: list = None, max_steps: int = 10):
        # LLM 客户端
        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        # 工具列表
        self.tools = tools if tools is not None else get_tools_for_patterns()
        # 最大执行步骤数
        self.max_steps = max_steps

    def create_plan(self, task: str) -> list:
        """LLM 分析任务并生成执行计划"""
        planning_prompt = (
            "你是一个任务规划专家。请将以下任务分解为具体的执行步骤。\n"
            "要求：\n"
            "1. 每个步骤要具体、可执行\n"
            "2. 如果某步骤需要搜索信息，请明确指出搜索关键词\n"
            "3. 如果某步骤需要计算，请明确指出计算公式\n"
            "4. 步骤之间要有逻辑顺序\n"
            "5. 用 JSON 格式返回，格式：{\"steps\": [\"步骤1描述\", \"步骤2描述\", ...]}\n"
        )

        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": planning_prompt},
                {"role": "user", "content": f"请为以下任务制定执行计划：\n{task}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        plan_data = json.loads(response.choices[0].message.content)
        return plan_data.get("steps", [task])

    def execute_step(self, step: str, context: str = "") -> str:
        """LLM 执行单个计划步骤（可能调用工具）"""
        tools_desc = "\n".join([
            f"- {t.name}: {t.description}" for t in self.tools
        ])

        execute_prompt = (
            "你是一个任务执行助手。请执行以下步骤，如果需要获取信息或计算，"
            "请明确说明需要使用哪个工具以及具体的参数。\n\n"
            f"可用工具：\n{tools_desc}\n\n"
            "如果你需要使用工具，请用以下 JSON 格式回复：\n"
            '{"use_tool": true, "tool_name": "工具名称", "tool_args": {"参数名": "参数值"}}\n'
            "如果不需要工具，请直接给出执行结果：\n"
            '{"use_tool": false, "result": "你的执行结果"}\n'
        )

        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": execute_prompt},
                {"role": "user", "content": f"上下文：{context}\n\n要执行的步骤：{step}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        try:
            decision = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return f"[执行错误] 无法解析 LLM 响应"

        if decision.get("use_tool"):
            # 需要调用工具
            tool_name = decision.get("tool_name", "")
            tool_args = decision.get("tool_args", {})
            tool = find_tool_by_name(self.tools, tool_name)
            if tool:
                result = tool.execute(**tool_args)
                return result.get("content", [{}])[0].get("text", "")
            else:
                return f"[错误] 未找到工具: {tool_name}"
        else:
            # 直接返回 LLM 的执行结果
            return decision.get("result", "")

    def synthesize_result(self, task: str, plan: list,
                          results: list) -> str:
        """LLM 汇总所有步骤的结果，生成最终答案"""
        # 构建计划+结果的对照文本
        execution_log = ""
        for i, (step, result) in enumerate(zip(plan, results), 1):
            execution_log += f"步骤{i}: {step}\n结果: {result[:200]}\n\n"

        synthesis_prompt = (
            "你是一个任务总结专家。请基于以下执行计划和各步骤的结果，"
            "生成一个完整、清晰的最终答案。"
        )

        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": synthesis_prompt},
                {"role": "user", "content": (
                    f"原始任务：{task}\n\n"
                    f"执行日志：\n{execution_log}\n"
                    f"请生成最终答案。"
                )}
            ],
            temperature=0.5
        )

        return response.choices[0].message.content or "无法生成最终答案"

    def run(self, task: str) -> str:
        """完整的 Plan-Execute 流程"""
        print(f"\n  📋 任务: {task}")
        print(f"{'─'*50}")

        # 阶段 1：制定计划
        print("  🧠 阶段 1：LLM 制定执行计划...")
        plan = self.create_plan(task)
        print(f"  📝 计划（共 {len(plan)} 步）：")
        for i, step in enumerate(plan, 1):
            print(f"      {i}. {step}")

        # 阶段 2：逐步执行
        print(f"\n  ⚙️ 阶段 2：逐步执行计划...")
        results = []
        context = ""  # 累积上下文
        for i, step in enumerate(plan, 1):
            if i > self.max_steps:
                print(f"  ⚠️ 达到最大步骤数 {self.max_steps}，停止执行")
                break
            print(f"\n  --- 步骤 {i}/{len(plan)} ---")
            print(f"  📌 执行: {step}")
            result = self.execute_step(step, context)
            print(f"  ✅ 结果: {result[:150]}...")
            results.append(result)
            context += f"\n步骤{i}结果: {result[:200]}"

        # 阶段 3：汇总
        print(f"\n  📊 阶段 3：LLM 汇总结果...")
        final_answer = self.synthesize_result(task, plan, results)

        return final_answer


# ==================== 直接测试 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  Plan-Execute Agent 自测")
    print("=" * 60)

    agent = PlanExecuteAgent()
    print(f"✅ Agent 初始化完成，{len(agent.tools)} 个工具可用\n")

    # 简单任务测试
    task = "帮我调研一下 Python 和深度学习的关系，并计算 15*7+3"
    print(f"  测试任务: {task}\n")
    try:
        result = agent.run(task)
        print(f"\n{'='*60}")
        print(f"  🎯 最终答案:\n{result}")
    except Exception as e:
        print(f"  ⚠️ LLM 调用失败: {e}")
        print(f"  💡 请确保 .env 中配置了有效的 OPENAI_API_KEY")
