"""
example.py — Day 13 完整演示：多 Agent 协作系统

演示内容：
1. 顺序协作 — 三个专家 Agent 流水线式协作
2. 并行协作 — 独立任务同时执行，对比顺序模式
3. 投票决策 — 多个 Agent 对同一问题投票
4. 管理者-工作者 — Manager 分解任务分配给 Specialist
5. 通信机制 — DirectMessenger + SharedBlackboard 实战
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import time
from agent_core import BaseAgent, SpecialistAgent, ManagerAgent
from coordinator import SequentialCoordinator, ParallelCoordinator, VotingCoordinator
from communication import Message, DirectMessenger, SharedBlackboard, PubSubSystem
from tools import get_agent_tools


def demo_sequential():
    """演示 1：顺序协作 — 三个专家流水线"""
    print("\n" + "=" * 60)
    print("  📋 演示 1：顺序协作 — 专家流水线")
    print("=" * 60)

    # 创建三个不同工具的专家 Agent
    researcher = SpecialistAgent(
        name="Researcher",
        specialty="信息搜索与分析",
        tools=get_agent_tools(["search"])
    )
    coder = SpecialistAgent(
        name="Coder",
        specialty="代码分析与优化",
        tools=get_agent_tools(["code_analysis"])
    )
    analyst = SpecialistAgent(
        name="Analyst",
        specialty="数据统计与分析",
        tools=get_agent_tools(["data_analysis"])
    )

    # 顺序协作：先搜索 → 再分析代码 → 最后分析数据
    coordinator = SequentialCoordinator([researcher, coder, analyst])

    tasks = [
        "搜索 Python 在 AI 开发中的最新趋势",
        "分析以下代码：def hello(): print('Hello'); class MyClass: pass",
        "分析数据：12, 45, 78, 23, 56, 89, 34",
    ]

    print(f"\n  🔄 顺序执行 {len(tasks)} 个任务（{len(coordinator.agents)} 个 Agent）...")
    try:
        results = coordinator.execute(tasks)
        for r in results:
            print(f"\n  📌 [{r['agent']}] {r['task'][:50]}...")
            print(f"  ✅ {r['result'][:200]}...")
            print(f"  ⏱ 耗时: {r['duration']}")
    except Exception as e:
        print(f"  ⚠️ LLM 调用失败: {e}")
        print(f"  💡 需要配置有效的 OPENAI_API_KEY")


def demo_parallel():
    """演示 2：并行协作 — 与顺序模式对比"""
    print("\n" + "=" * 60)
    print("  📋 演示 2：并行协作 — 效率对比")
    print("=" * 60)

    # 创建三个独立工作的 Agent
    agents = [
        SpecialistAgent(name="Agent-A", specialty="搜索", tools=get_agent_tools(["search"])),
        SpecialistAgent(name="Agent-B", specialty="搜索", tools=get_agent_tools(["search"])),
        SpecialistAgent(name="Agent-C", specialty="搜索", tools=get_agent_tools(["search"])),
    ]

    tasks = [
        "搜索机器学习的最新进展",
        "搜索深度学习的最新进展",
        "搜索神经网络的最新进展",
    ]

    # 顺序执行
    print("\n  -- 顺序执行 --")
    seq_coordinator = SequentialCoordinator(agents)
    try:
        seq_results = seq_coordinator.execute(tasks)
    except Exception as e:
        print(f"  ⚠️ 顺序执行失败: {e}")
        return

    # 并行执行
    print("\n  -- 并行执行 --")
    par_coordinator = ParallelCoordinator(agents)
    try:
        par_results = par_coordinator.execute(tasks)
    except Exception as e:
        print(f"  ⚠️ 并行执行失败: {e}")
        return

    print(f"\n  📊 对比：并行执行可显著减少总等待时间（当任务独立时）")


def demo_voting():
    """演示 3：投票决策"""
    print("\n" + "=" * 60)
    print("  📋 演示 3：投票决策")
    print("=" * 60)

    # 三个不同视角的 Agent 对同一问题投票
    voters = [
        SpecialistAgent(name="技术专家", specialty="技术可行性", tools=get_agent_tools(["search"])),
        SpecialistAgent(name="产品专家", specialty="产品价值", tools=get_agent_tools(["search"])),
        SpecialistAgent(name="用户代表", specialty="用户体验", tools=get_agent_tools(["search"])),
    ]

    coordinator = VotingCoordinator(voters)
    question = "AI Agent 技术目前最大的应用价值是什么？请用一句话回答"

    print(f"\n  ❓ 投票问题: {question}\n")
    try:
        winner, votes = coordinator.execute_voting(question)
        print(f"\n  🏆 获胜答案（{votes}/{len(voters)} 票）:")
        print(f"  {winner}")
    except Exception as e:
        print(f"  ⚠️ LLM 调用失败: {e}")


def demo_manager_worker():
    """演示 4：管理者-工作者模式"""
    print("\n" + "=" * 60)
    print("  📋 演示 4：管理者-工作者模式")
    print("=" * 60)

    # 创建团队
    researcher = SpecialistAgent(name="研究员", specialty="信息搜索", tools=get_agent_tools(["search"]))
    analyst = SpecialistAgent(name="数据分析师", specialty="数据分析", tools=get_agent_tools(["data_analysis"]))
    writer = SpecialistAgent(name="报告撰写员", specialty="报告撰写", tools=get_agent_tools(["format_report"]))

    # 管理者协调团队
    manager = ManagerAgent(name="项目经理", workers=[researcher, analyst, writer])

    task = "做一个关于人工智能发展趋势的简要调研报告"

    print(f"\n  🎯 任务: {task}\n")
    try:
        output = manager.assign_and_execute(task)
        print(f"\n  📊 最终报告:")
        print(f"  {output.get('summary', '无结果')}")
    except Exception as e:
        print(f"  ⚠️ 执行失败: {e}")


def demo_communication():
    """演示 5：Agent 通信机制"""
    print("\n" + "=" * 60)
    print("  📋 演示 5：Agent 通信机制")
    print("=" * 60)

    # 创建通信基础设施
    messenger = DirectMessenger()
    blackboard = SharedBlackboard()
    pubsub = PubSubSystem()

    # 模拟 Agent 间的通信
    print("\n  -- 点对点消息 --")
    messenger.send(Message(sender="Researcher", receiver="Analyst", content="搜索完成，数据已写入黑板"))
    messenger.send(Message(sender="Researcher", receiver="Writer", content="请开始撰写报告初稿"))
    for msg in messenger.receive("Analyst"):
        print(f"  📨 {msg.sender} → {msg.receiver}: {msg.content}")
    for msg in messenger.receive("Writer"):
        print(f"  📨 {msg.sender} → {msg.receiver}: {msg.content}")

    print("\n  -- 共享黑板 --")
    blackboard.write("research_data", "AI 技术趋势：大模型、多模态、Agent...", writer="Researcher")
    blackboard.write("analysis_result", "AI 市场规模预计 2026 年达 3000 亿美元", writer="Analyst")
    print(blackboard.display())

    print("\n  -- 发布订阅 --")

    def on_research_complete(msg):
        print(f"    [通知 Analyst] {msg}")

    def on_report_ready(msg):
        print(f"    [通知 Manager] {msg}")

    pubsub.subscribe("research.done", on_research_complete)
    pubsub.subscribe("report.ready", on_report_ready)
    pubsub.publish("research.done", "研究阶段完成，可以开始分析")
    pubsub.publish("report.ready", "最终报告已生成")


def main():
    """主函数"""
    print("=" * 60)
    print("  Day 13: 多 Agent 协作系统")
    print("  顺序 | 并行 | 投票 | 管理者 | 通信")
    print("=" * 60)

    try:
        demo_communication()  # 通信演示不需要 LLM，先运行

        demo_sequential()
        demo_parallel()
        demo_voting()
        demo_manager_worker()

        print("\n" + "=" * 60)
        print("  ✅ 所有演示完成！")
        print("=" * 60)
        print("\n  💡 Day 13 关键要点：")
        print("    1. 顺序协作 — Agent 按序执行，适合有依赖的任务链")
        print("    2. 并行协作 — Agent 同时执行，适合独立子任务，大幅减少总时间")
        print("    3. 投票决策 — 多个 Agent 多角度作答，投票选出最佳答案")
        print("    4. 管理者-工作者 — Manager 分解任务，Worker 各司其职")
        print("    5. 通信机制 — 点对点消息 + 共享黑板 + 发布订阅")

    except Exception as e:
        print(f"\n  ❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
