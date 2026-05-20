"""
coordinator.py — 多 Agent 协调策略

三种协调模式：
1. SequentialCoordinator — 顺序执行（适合有依赖的任务链）
2. ParallelCoordinator — 并行执行（适合独立子任务）
3. VotingCoordinator — 投票决策（适合需要共识的决策）

设计原则：零外部依赖，与 Agent 核心解耦
"""
import time
import asyncio
from collections import Counter
from agent_core import BaseAgent
from typing import List


class SequentialCoordinator:
    """顺序协调器 — Agent 逐个执行任务，适合有依赖关系的场景"""

    def __init__(self, agents: List[BaseAgent] = None):
        self.agents = agents or []

    def add_agent(self, agent: BaseAgent) -> None:
        self.agents.append(agent)

    def execute(self, tasks: list) -> list:
        """顺序执行：每个 Agent 依次处理自己的任务"""
        if len(tasks) != len(self.agents):
            raise ValueError(f"任务数 ({len(tasks)}) 与 Agent 数 ({len(self.agents)}) 不匹配")

        results = []
        total_start = time.time()

        for agent, task in zip(self.agents, tasks):
            print(f"\n  ▶ [{agent.name}] 开始执行: {task[:60]}...")
            start = time.time()
            result = agent.execute(task)
            elapsed = time.time() - start
            results.append({"agent": agent.name, "task": task, "result": result, "duration": f"{elapsed:.2f}s"})
            print(f"  ✓ [{agent.name}] 完成（耗时 {elapsed:.2f}s）: {result[:100]}...")

        total_time = time.time() - total_start
        print(f"\n  ⏱ 顺序执行总耗时: {total_time:.2f}s")
        return results


class ParallelCoordinator:
    """并行协调器 — Agent 同时执行任务，适合无依赖的独立子任务"""

    def __init__(self, agents: List[BaseAgent] = None):
        self.agents = agents or []

    def add_agent(self, agent: BaseAgent) -> None:
        self.agents.append(agent)

    async def _execute_async(self, agent: BaseAgent, task: str) -> dict:
        """异步执行单个 Agent 的任务"""
        start = time.time()
        # 在真实异步环境中用 run_in_executor 运行同步的 LLM 调用
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, agent.execute, task)
        elapsed = time.time() - start
        return {"agent": agent.name, "task": task, "result": result, "duration": f"{elapsed:.2f}s"}

    def execute(self, tasks: list) -> list:
        """并行执行：所有 Agent 同时开始处理各自任务"""
        if len(tasks) != len(self.agents):
            raise ValueError(f"任务数 ({len(tasks)}) 与 Agent 数 ({len(self.agents)}) 不匹配")

        print(f"\n  ⚡ 并行启动 {len(self.agents)} 个 Agent...")
        total_start = time.time()

        async def run_all():
            coroutines = [
                self._execute_async(agent, task)
                for agent, task in zip(self.agents, tasks)
            ]
            return await asyncio.gather(*coroutines)

        results = asyncio.run(run_all())

        for r in results:
            print(f"  ✓ [{r['agent']}] 完成（{r['duration']}）: {r['result'][:100]}...")

        total_time = time.time() - total_start
        print(f"\n  ⏱ 并行执行总耗时: {total_time:.2f}s")
        # 理论加速比
        individual_times = [float(r["duration"].replace("s", "")) for r in results]
        if individual_times:
            print(f"  📊 并行效率: 总时间={total_time:.2f}s, 最长单任务={max(individual_times):.2f}s")
        return results


class VotingCoordinator:
    """投票协调器 — 多个 Agent 独立作答，投票选出最佳答案"""

    def __init__(self, agents: List[BaseAgent] = None):
        self.agents = agents or []

    def add_agent(self, agent: BaseAgent) -> None:
        self.agents.append(agent)

    def collect_votes(self, answers: List[str]) -> Counter:
        """统计投票结果"""
        return Counter(answers)

    def decide(self, vote_count: Counter) -> tuple:
        """根据投票结果做出决策，返回 (获胜答案, 票数)"""
        if not vote_count:
            return ("无有效答案", 0)
        winner = vote_count.most_common(1)[0]
        return winner

    def execute_voting(self, task: str) -> tuple:
        """完整投票流程：所有 Agent 独立作答 → 收集 → 投票 → 决定"""
        print(f"\n  🗳 投票模式：{len(self.agents)} 个 Agent 各自作答...")

        # 阶段 1：每个 Agent 独立作答
        answers = []
        for agent in self.agents:
            print(f"  ▶ [{agent.name}] 思考中...")
            answer = agent.execute(task)
            answers.append(answer)
            print(f"  ✓ [{agent.name}]: {answer[:120]}...")

        # 阶段 2：统计投票
        print(f"\n  📊 投票统计...")
        vote_count = self.collect_votes(answers)
        for answer, count in vote_count.items():
            print(f"      {count} 票: {answer[:80]}...")

        # 阶段 3：决定最终答案
        winner, votes = self.decide(vote_count)
        print(f"\n  🏆 最终决定: {winner[:200]}... ({votes}/{len(self.agents)} 票)")
        return winner, votes


# ==================== 直接测试 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  协调器测试（无 LLM 模式）")
    print("=" * 60)

    # 创建简单的测试 Agent（不使用 LLM）
    class MockAgent:
        def __init__(self, name, response):
            self.name = name
            self._response = response

        def execute(self, task):
            time.sleep(0.1)  # 模拟工作
            return f"{self._response}: {task[:30]}"

    # 测试顺序协调
    agents = [MockAgent("A", "分析结果"), MockAgent("B", "搜索结果"), MockAgent("C", "计算答案")]
    print("\n📋 顺序协调测试：")
    sc = SequentialCoordinator(agents)
    results = sc.execute(["任务1", "任务2", "任务3"])

    # 测试投票
    print("\n🗳 投票协调测试：")
    voters = [MockAgent("V1", "方案A"), MockAgent("V2", "方案B"), MockAgent("V3", "方案A")]
    vc = VotingCoordinator(voters)
    winner, votes = vc.execute_voting("选择最优方案")
