"""
agent_core.py — 真实 LLM 驱动的 Multi-Agent 核心

Agent 类型：
1. BaseAgent — 基类，LLM 推理 + 工具调用循环
2. SpecialistAgent — 领域专家 Agent
3. ManagerAgent — 管理 Agent（任务分解 + 分配）

设计原则：
- 每个 Agent 拥有独立的 LLM 客户端和工具集
- 通过 system_prompt 区分角色和专业领域
- 支持 ReAct 工具调用循环
- 零 LangChain 依赖
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

from openai import OpenAI
import json
from typing import Optional
from tools import get_agent_tools, find_tool, tools_to_openai_format


class BaseAgent:
    """Agent 基类 — 封装 LLM 调用和工具使用能力"""

    def __init__(self, name: str, role: str, tools: list = None,
                 system_prompt: str = None, max_iterations: int = 5):
        self.name = name              # Agent 名称
        self.role = role              # Agent 角色描述
        self.tools = tools or []      # 分配给该 Agent 的工具
        self.max_iterations = max_iterations  # 最大工具调用次数
        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

        # 角色系统提示 — 定义 Agent 的行为和专业领域
        self.system_prompt = system_prompt or (
            f"你是 {name}，角色是 {role}。\n"
            "你可以使用工具来获取信息并完成任务。\n"
            "分析用户需求，使用合适的工具，基于工具结果生成准确回复。"
        )

    def think(self, task: str, context: str = "") -> str:
        """让 Agent 对任务进行推理（单次 LLM 调用，不使用工具）"""
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"背景信息：{context}\n\n任务：{task}\n\n请分析和思考这个任务。"}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content or ""

    def execute(self, task: str, context: str = "") -> str:
        """执行任务 — 包含完整的工具调用循环"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"背景信息：{context}\n\n任务：{task}" if context else task}
        ]

        openai_tools = tools_to_openai_format(self.tools) if self.tools else None

        for iteration in range(self.max_iterations):
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=openai_tools,
                tool_choice="auto" if openai_tools else None,
                temperature=0.3
            )

            msg = response.choices[0].message

            # 无工具调用 → 任务完成
            if not msg.tool_calls:
                return msg.content or f"[{self.name}] 任务完成"

            # 执行工具调用
            messages.append(msg)
            for tc in msg.tool_calls:
                tool = find_tool(self.tools, tc.function.name)
                args = json.loads(tc.function.arguments)
                if tool:
                    result = tool.execute(**args)
                    tool_output = result["content"][0]["text"]
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_output
                    })

        return f"[{self.name}] 任务执行超时（达到最大步骤数 {self.max_iterations}）"


class SpecialistAgent(BaseAgent):
    """专业 Agent — 特定领域的专家"""

    def __init__(self, name: str, specialty: str, tools: list = None):
        # 为专家 Agent 构建专门的系统提示
        system_prompt = (
            f"你是 {name}，一位专注于 {specialty} 的专家。\n"
            f"你的专业领域是{specialty}，你应该从这个角度分析所有问题。\n"
            "使用工具获取信息，基于专业知识给出深入的分析。\n"
            "回复要体现专家的专业水准，使用领域术语。"
        )
        super().__init__(name=name, role=f"{specialty}专家", tools=tools, system_prompt=system_prompt)
        self.specialty = specialty


class ManagerAgent(BaseAgent):
    """管理 Agent — 任务分解、分配和汇总"""

    def __init__(self, name: str = "Manager", workers: list = None):
        system_prompt = (
            f"你是 {name}，一位项目经理。\n"
            "你的职责是：\n"
            "1. 分析复杂任务，将其分解为子任务\n"
            "2. 将子任务分配给合适的团队成员\n"
            "3. 汇总各成员的结果，形成完整答案\n"
            "使用 JSON 格式回复任务分解。"
        )
        super().__init__(name=name, role="项目经理", tools=None, system_prompt=system_prompt)
        self.workers = workers or []  # 团队成员（其他 Agent）

    def add_worker(self, worker: BaseAgent) -> None:
        """添加团队成员"""
        self.workers.append(worker)

    def decompose_task(self, task: str) -> list:
        """LLM 驱动的任务分解"""
        workers_desc = "\n".join([
            f"- {w.name}: {w.role}" + (f"（专长：{w.specialty}）" if isinstance(w, SpecialistAgent) else "")
            for w in self.workers
        ])

        decompose_prompt = (
            "你是一个任务分解专家。请将以下任务分解为 2-4 个子任务，"
            "并为每个子任务指派最合适的处理者。\n\n"
            f"团队成员：\n{workers_desc}\n\n"
            "返回 JSON 格式：\n"
            '{"subtasks": [{"task": "子任务描述", "assignee": "成员名称", "reason": "指派理由"}]}'
        )

        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": decompose_prompt},
                {"role": "user", "content": f"请分解以下任务：{task}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        try:
            data = json.loads(response.choices[0].message.content)
            return data.get("subtasks", [{"task": task, "assignee": self.workers[0].name if self.workers else "none"}])
        except json.JSONDecodeError:
            return [{"task": task, "assignee": self.workers[0].name if self.workers else "none"}]

    def assign_and_execute(self, task: str) -> dict:
        """分解任务 → 分配 → 收集结果 → 汇总"""
        print(f"\n  👔 [{self.name}] 开始管理任务: {task[:80]}...")

        # 步骤 1：分解任务
        subtasks = self.decompose_task(task)
        print(f"  📋 [{self.name}] 任务分解为 {len(subtasks)} 个子任务：")
        for st in subtasks:
            print(f"      • {st['task'][:60]}... → {st['assignee']}")

        # 步骤 2：分配并执行
        results = []
        worker_map = {w.name: w for w in self.workers}

        for st in subtasks:
            assignee = st.get("assignee", "")
            subtask_desc = st.get("task", "")
            worker = worker_map.get(assignee)

            if worker:
                print(f"  ▶ [{assignee}] 执行: {subtask_desc[:60]}...")
                worker_result = worker.execute(subtask_desc)
                results.append({
                    "subtask": subtask_desc,
                    "assignee": assignee,
                    "result": worker_result
                })
                print(f"  ✓ [{assignee}] 完成: {worker_result[:100]}...")
            else:
                results.append({
                    "subtask": subtask_desc,
                    "assignee": assignee,
                    "result": f"[错误] 未找到团队成员: {assignee}"
                })

        # 步骤 3：汇总结果
        print(f"  📊 [{self.name}] 汇总结果...")
        summary = self._synthesize(task, results)
        return {"task": task, "subtasks": results, "summary": summary}

    def _synthesize(self, task: str, results: list) -> str:
        """LLM 汇总各子任务结果"""
        results_text = "\n".join([
            f"子任务{i+1}: {r['subtask']}\n执行者: {r['assignee']}\n结果: {r['result'][:300]}"
            for i, r in enumerate(results)
        ])

        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个项目经理，汇总团队成员的执行结果形成完整报告。"},
                {"role": "user", "content": f"原始任务：{task}\n\n各子任务结果：\n{results_text}\n\n请生成完整报告。"}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content or "汇总失败"
