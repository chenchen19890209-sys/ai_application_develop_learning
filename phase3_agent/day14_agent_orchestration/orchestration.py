"""
orchestration.py — 原生 Python Agent 编排系统

核心组件（零 LangGraph 依赖）：
1. WorkflowStep — 工作流步骤定义
2. AgentWorkflow — 顺序工作流（支持条件路由）
3. AgentPipeline — 数据处理管道
4. ConditionalRouter — LLM 驱动的条件路由器
5. AgentOrchestrator — 顶层编排控制器

编排模式：
- 条件路由：LLM 分析输入 → 路由到不同处理器
- 顺序管道：Agent1 → Agent2 → Agent3 依次处理
- 并行聚合：多个 Agent 并行处理 → LLM 汇总
- 自改进循环：Agent 输出 → 检查 → 不满足则重新执行
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

from openai import OpenAI
import json
import time
import asyncio
from typing import Dict, Callable, Optional
from tools import get_orchestration_tools, find_tool, tools_to_openai_format


# ==================== 工作流步骤 ====================

class WorkflowStep:
    """工作流中的单个执行步骤"""

    def __init__(self, name: str, agent_func: Callable, task_template: str = None, condition: Callable = None):
        self.name = name                          # 步骤名称
        self.agent_func = agent_func              # 执行函数
        self.task_template = task_template or ""  # 任务模板（支持 {input} 占位符）
        self.condition = condition                # 条件函数（可选，用于条件路由）
        self.output = None                        # 步骤输出（执行后设置）


# ==================== Agent 工作流 ====================

class AgentWorkflow:
    """Agent 工作流编排器 — 支持顺序执行、条件路由和循环"""

    def __init__(self, name: str = "default"):
        self.name = name
        self.steps: list[WorkflowStep] = []
        self.routes: dict = {}  # 条件路由表：{(from_step, condition_result): to_step}

    def add_step(self, step: WorkflowStep) -> None:
        """添加工作流步骤"""
        self.steps.append(step)

    def add_router(self, from_step: str, condition_func: Callable,
                   true_step: str, false_step: str) -> None:
        """添加条件路由"""
        self.routes[(from_step, "true")] = true_step
        self.routes[(from_step, "false")] = false_step
        # 保存条件函数引用
        for step in self.steps:
            if step.name == from_step:
                step.condition = condition_func

    def run(self, initial_input: str) -> dict:
        """执行工作流"""
        print(f"\n{'='*50}")
        print(f"  工作流 [{self.name}] 开始执行")
        print(f"{'='*50}")

        current_input = initial_input
        results = {}

        for i, step in enumerate(self.steps):
            print(f"\n  ▶ 步骤 {i+1}/{len(self.steps)}: [{step.name}]")

            # 检查是否需要条件路由
            if step.condition and current_input:
                condition_result = step.condition(current_input)
                route_key = (step.name, "true" if condition_result else "false")
                next_step_name = self.routes.get(route_key)
                if next_step_name:
                    print(f"  🔀 条件路由: {step.name} → {next_step_name}")

            # 执行步骤
            task = step.task_template.format(input=current_input) if step.task_template else current_input

            try:
                result = step.agent_func(task)
                step.output = result
                results[step.name] = result
                current_input = result  # 当前步骤的输出成为下一步的输入
                print(f"  ✓ [{step.name}] 完成: {str(result)[:120]}...")
            except Exception as e:
                print(f"  ✗ [{step.name}] 失败: {e}")
                results[step.name] = f"错误: {e}"

        print(f"\n{'='*50}")
        print(f"  工作流 [{self.name}] 执行完成")
        print(f"{'='*50}")
        return results

    def visualize(self) -> str:
        """生成 ASCII 流程图"""
        if not self.steps:
            return "[空工作流]"
        lines = [f"工作流 [{self.name}]:"]
        for i, step in enumerate(self.steps):
            arrow = "  ↓" if i < len(self.steps) - 1 else "  ✗"
            lines.append(f"  [{step.name}]")
            if step.condition:
                lines.append(f"    ↙↘ (条件分支)")
            if i < len(self.steps) - 1:
                next_step = self.steps[i + 1]
                route_key = (step.name, "true")
                if route_key in self.routes:
                    lines.append(f"    ├─ Yes → [{self.routes[route_key]}]")
                    lines.append(f"    └─ No → [{self.routes.get((step.name, 'false'), next_step.name)}]")
                else:
                    lines.append(f"    ↓")
        return "\n".join(lines)


# ==================== Agent 管道 ====================

class AgentPipeline:
    """Agent 管道 — 数据依次经过多个 Agent 处理"""

    def __init__(self, agents: list = None):
        self.agents = agents or []

    def add_agent(self, agent_func: Callable, name: str = "") -> None:
        self.agents.append((name or f"Agent{len(self.agents)+1}", agent_func))

    def process(self, input_data: str) -> list:
        """依次通过每个 Agent 处理数据"""
        current = input_data
        results = []

        for name, agent_func in self.agents:
            print(f"  ▶ [{name}] 处理中...")
            start = time.time()
            try:
                current = agent_func(current)
                elapsed = time.time() - start
                results.append({"agent": name, "output": current, "duration": f"{elapsed:.2f}s"})
                print(f"  ✓ [{name}] 完成（{elapsed:.2f}s）: {str(current)[:100]}...")
            except Exception as e:
                results.append({"agent": name, "output": f"错误: {e}", "duration": "0s"})
                print(f"  ✗ [{name}] 失败: {e}")

        return results


# ==================== 条件路由器 ====================

class ConditionalRouter:
    """LLM 驱动的条件路由器 — 分析输入并决定处理路径"""

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

    def classify(self, query: str, categories: list) -> str:
        """LLM 将查询分类到预定义的类别中"""
        categories_text = "\n".join([f"- {c}" for c in categories])

        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": (
                    "你是一个查询分类器。将用户的查询归类到最匹配的类别中。\n"
                    f"可用类别：\n{categories_text}\n\n"
                    "返回 JSON 格式：{\"category\": \"选中的类别\", \"confidence\": \"high/medium/low\"}"
                )},
                {"role": "user", "content": query}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        try:
            data = json.loads(response.choices[0].message.content)
            return data.get("category", categories[0])
        except json.JSONDecodeError:
            return categories[0]

    def route(self, query: str, route_map: Dict[str, Callable]) -> str:
        """分类查询并路由到对应的处理器"""
        categories = list(route_map.keys())
        category = self.classify(query, categories)
        print(f"  🔀 路由决策: \"{query[:50]}...\" → [{category}]")

        handler = route_map.get(category)
        if handler:
            return handler(query)
        return f"未找到类别 '{category}' 的处理器"


# ==================== 顶层编排器 ====================

class AgentOrchestrator:
    """编排器 — 组合工作流、管道和路由的顶层控制器"""

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        self.tools = get_orchestration_tools()
        self._openai_tools = tools_to_openai_format(self.tools)

    def _create_agent_function(self, name: str, system_prompt: str):
        """创建一个 Agent 执行函数（闭包）"""
        def agent_func(task: str) -> str:
            """Agent 执行函数 — 包含工具调用循环"""
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task}
            ]

            for _ in range(5):
                response = self.client.chat.completions.create(
                    model=OPENAI_MODEL, messages=messages,
                    tools=self._openai_tools, tool_choice="auto", temperature=0.3
                )
                msg = response.choices[0].message
                if not msg.tool_calls:
                    return msg.content or ""
                messages.append(msg)
                for tc in msg.tool_calls:
                    tool = find_tool(self.tools, tc.function.name)
                    args = json.loads(tc.function.arguments)
                    if tool:
                        result = tool.execute(**args)
                        messages.append({
                            "role": "tool", "tool_call_id": tc.id,
                            "content": result["content"][0]["text"]
                        })
            return "Agent 执行超时"

        return agent_func

    def create_workflow(self, workflow_type: str) -> AgentWorkflow:
        """创建不同类型的工作流"""

        if workflow_type == "research_pipeline":
            # 调研管道：搜索 → 分析 → 报告
            wf = AgentWorkflow("调研管道")
            wf.add_step(WorkflowStep(
                "搜索信息", self._create_agent_function("Searcher", "你是信息搜索专家，使用 search 工具搜索相关信息。"),
                task_template="搜索以下主题的信息：{input}"
            ))
            wf.add_step(WorkflowStep(
                "分析整理", self._create_agent_function("Analyst", "你是信息分析专家，基于搜索结果进行深度分析。不调用工具。"),
                task_template="分析以下信息并提取关键要点：{input}"
            ))
            wf.add_step(WorkflowStep(
                "生成报告", self._create_agent_function("Writer", "你是报告撰写专家，基于分析结果生成结构化报告。不调用工具。"),
                task_template="基于以下分析生成一份简洁的报告：{input}"
            ))
            return wf

        elif workflow_type == "parallel_analysis":
            # 并行分析：多个视角同时分析
            wf = AgentWorkflow("并行分析")

            def parallel_analysis(task: str) -> str:
                """并行执行多个分析视角"""
                perspectives = [
                    ("技术视角", "你从技术可行性角度分析问题。"),
                    ("商业视角", "你从商业价值和市场角度分析问题。"),
                    ("用户视角", "你从用户体验和需求角度分析问题。"),
                ]

                async def analyze_one(name: str, prompt: str):
                    loop = asyncio.get_event_loop()
                    func = self._create_agent_function(name, prompt)
                    return await loop.run_in_executor(None, func, task)

                async def run_all():
                    coroutines = [analyze_one(name, prompt) for name, prompt in perspectives]
                    return await asyncio.gather(*coroutines)

                all_results = asyncio.run(run_all())
                combined = "\n".join([
                    f"【{perspectives[i][0]}】{result}"
                    for i, result in enumerate(all_results)
                ])
                return combined

            wf.add_step(WorkflowStep("多角度分析", parallel_analysis))
            wf.add_step(WorkflowStep(
                "汇总", self._create_agent_function("Synthesizer", "你综合多个角度的分析，生成完整报告。不调用工具。"),
                task_template="综合以下多角度分析结果：{input}"
            ))
            return wf

        elif workflow_type == "self_improve":
            # 自改进循环：检查 → 重写 → 再检查
            wf = AgentWorkflow("自改进")

            def write_and_improve(task: str) -> str:
                """写初稿并根据反馈改进"""
                writer = self._create_agent_function("Writer", "你是技术文档撰写专家。")
                reviewer = self._create_agent_function("Reviewer", "你是严格的审阅者，指出问题并要求改进。")

                draft = writer(task)
                print(f"  📝 初稿: {draft[:100]}...")

                for iteration in range(2):  # 最多改进 2 次
                    review_prompt = f"审阅以下内容，指出问题：\n\n{draft}"
                    feedback = reviewer(review_prompt)
                    print(f"  🔍 审阅意见 {iteration+1}: {feedback[:100]}...")

                    # 判断是否需要改进
                    if "没有问题" in feedback or "很好" in feedback:
                        print(f"  ✅ 审阅通过")
                        break

                    improve_prompt = f"根据以下审阅意见改进内容：\n\n原文：{draft}\n\n审阅意见：{feedback}"
                    draft = writer(improve_prompt)
                    print(f"  ✏️ 改进稿 {iteration+1}: {draft[:100]}...")

                return draft

            wf.add_step(WorkflowStep("撰写与改进", write_and_improve))
            return wf

        else:
            raise ValueError(f"未知工作流类型: {workflow_type}")

    def execute_workflow(self, workflow_type: str, input_data: str) -> dict:
        """创建并执行工作流"""
        workflow = self.create_workflow(workflow_type)
        print(workflow.visualize())
        return workflow.run(input_data)


# ==================== 直接测试 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  编排系统自测")
    print("=" * 60)

    # 创建简单模拟函数测试工作流
    def mock_step1(input_text):
        return f"[步骤1处理] {input_text}"

    def mock_step2(input_text):
        return f"[步骤2处理] {input_text}"

    wf = AgentWorkflow("测试工作流")
    wf.add_step(WorkflowStep("步骤1", mock_step1))
    wf.add_step(WorkflowStep("步骤2", mock_step2))
    print(f"\n{'-'*40}")
    print(wf.visualize())
    results = wf.run("初始输入")
    print(f"\n  结果: {results}")
