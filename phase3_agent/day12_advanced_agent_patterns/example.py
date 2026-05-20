"""
example.py — Day 12 完整演示：三种高级 Agent 模式对比

演示内容：
1. Plan-Execute — 多步骤调研任务
2. ReWOO — 并行工具调用
3. Self-Ask — 层层追问的复杂推理
4. 三种模式对比 — 同一任务不同模式的效率差异
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from plan_execute import PlanExecuteAgent
from rewoo import ReWOOAgent
from self_ask import SelfAskAgent
import time


def demo_plan_execute():
    """演示 1：Plan-Execute 模式 — 多步骤调研"""
    print("\n" + "=" * 60)
    print("  📋 演示 1：Plan-Execute — 多步骤调研")
    print("=" * 60)

    agent = PlanExecuteAgent()
    task = "帮我调研一下 Python 在 AI 开发中的地位，并计算 2026 - 1991 的结果"

    print(f"\n  🎯 任务: {task}\n")
    try:
        result = agent.run(task)
        print(f"\n  ✅ 最终答案:\n  {result}")
    except Exception as e:
        print(f"\n  ⚠️ LLM 调用失败: {e}")
        print(f"  💡 Plan-Execute 需要有效的 API Key")


def demo_rewoo():
    """演示 2：ReWOO 模式 — 并行工具调用"""
    print("\n" + "=" * 60)
    print("  📋 演示 2：ReWOO — 并行工具调用")
    print("=" * 60)

    agent = ReWOOAgent()
    task = "搜索深度学习的信息和神经网络的信息，然后计算 100 + 200 * 3 的结果"

    print(f"\n  🎯 任务: {task}\n")
    try:
        result = agent.run(task)
        print(f"\n  ✅ 最终答案:\n  {result}")
    except Exception as e:
        print(f"\n  ⚠️ LLM 调用失败: {e}")
        print(f"  💡 ReWOO 需要有效的 API Key")


def demo_self_ask():
    """演示 3：Self-Ask 模式 — 层层追问推理"""
    print("\n" + "=" * 60)
    print("  📋 演示 3：Self-Ask — 追问链推理")
    print("=" * 60)

    agent = SelfAskAgent()
    task = "Transformer 架构的提出者是谁？这个架构主要解决了什么问题？"

    print(f"\n  🎯 问题: {task}\n")
    try:
        result = agent.run(task)
        print(f"\n  ✅ 最终答案:\n  {result}")
    except Exception as e:
        print(f"\n  ⚠️ LLM 调用失败: {e}")
        print(f"  💡 Self-Ask 需要有效的 API Key")


def demo_comparison():
    """演示 4：三种模式效率对比"""
    print("\n" + "=" * 60)
    print("  📋 演示 4：三种模式对比分析")
    print("=" * 60)

    print("""
  ┌───────────────┬──────────────────┬──────────────────┬──────────────────┐
  │    维度        │   Plan-Execute   │      ReWOO       │     Self-Ask     │
  ├───────────────┼──────────────────┼──────────────────┼──────────────────┤
  │ 核心思路       │ 先制定完整计划   │ 占位符+批量执行   │ 追问链式推理     │
  │ LLM 调用次数   │ 中等 (3-N次)    │ 较少 (3次)       │ 较多 (N次追问)   │
  │ 工具调用方式   │ 逐步串行         │ 批量并行         │ 按需串行         │
  │ 适用场景       │ 多步骤复杂任务   │ 无依赖的并行查询  │ 需要递进推理     │
  │ 可解释性       │ ⭐⭐⭐ 高       │ ⭐⭐ 中          │ ⭐⭐⭐ 高       │
  │ 执行效率       │ ⭐⭐ 中          │ ⭐⭐⭐ 高        │ ⭐ 较低         │
  │ 灵活性         │ ⭐⭐ 中          │ ⭐⭐ 中          │ ⭐⭐⭐ 高       │
  └───────────────┴──────────────────┴──────────────────┴──────────────────┘

  💡 选择建议：
  - 任务有明确步骤、需要可解释 → Plan-Execute
  - 需要多个独立查询、追求效率 → ReWOO
  - 问题需要层层递进、上下文依赖 → Self-Ask
  - 简单对话、单步查询 → ReAct（Day09）
    """)


def main():
    """主函数"""
    print("=" * 60)
    print("  Day 12: 高级 Agent 模式")
    print("  Plan-Execute | ReWOO | Self-Ask")
    print("=" * 60)

    try:
        demo_plan_execute()
        demo_rewoo()
        demo_self_ask()
        demo_comparison()

        print("\n" + "=" * 60)
        print("  ✅ 所有演示完成！")
        print("=" * 60)
        print("\n  💡 Day 12 关键要点：")
        print("    1. Plan-Execute: 先规划再执行，适合结构化的多步骤任务")
        print("    2. ReWOO: 用占位符批量执行工具调用，减少 LLM 调用次数")
        print("    3. Self-Ask: 通过追问链层层递进，适合需要推理的复杂问题")
        print("    4. 三种模式各有优势，根据任务特点选择")
        print("    5. 所有模式都使用原生 openai SDK，零框架依赖")

    except Exception as e:
        print(f"\n  ❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
