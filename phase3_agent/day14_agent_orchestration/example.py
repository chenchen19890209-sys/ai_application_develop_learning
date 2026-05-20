"""
example.py — Day 14 完整演示：Agent 编排系统

演示内容：
1. 条件路由 — 根据查询类型自动路由到不同处理器
2. Agent 管道 — 搜索 → 分析 → 报告 流水线
3. 并行聚合 — 多角度分析后汇总
4. 自改进循环 — 撰写 → 审阅 → 改进
5. 完整编排器 — 组合所有模式
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestration import AgentOrchestrator, AgentWorkflow, WorkflowStep, ConditionalRouter


def demo_conditional_routing():
    """演示 1：条件路由 — 自动分类与路由"""
    print("\n" + "=" * 60)
    print("  📋 演示 1：条件路由")
    print("=" * 60)

    try:
        router = ConditionalRouter()

        # 不同类别的查询
        queries = [
            "帮我算一下 12345 * 6789",
            "北京今天天气如何？",
            "什么是机器学习？请介绍一下。",
        ]
        categories = ["数学计算", "天气查询", "知识问答", "文本分析"]

        for q in queries:
            print(f"\n  ❓ 查询: {q}")
            try:
                category = router.classify(q, categories)
                print(f"  🔀 分类结果: {category}")
            except Exception as e:
                print(f"  ⚠️ 分类失败: {e}")
    except Exception as e:
        print(f"  ⚠️ 路由器初始化失败: {e}")


def demo_pipeline():
    """演示 2：Agent 管道 — 搜索→分析→报告"""
    print("\n" + "=" * 60)
    print("  📋 演示 2：调研管道 — 搜索→分析→报告")
    print("=" * 60)

    try:
        orchestrator = AgentOrchestrator()
        task = "Python 在 AI 开发中的应用"

        print(f"\n  🎯 任务: {task}")
        results = orchestrator.execute_workflow("research_pipeline", task)

        print(f"\n  📊 管道结果：")
        for step_name, result in results.items():
            print(f"  [{step_name}]: {str(result)[:200]}...")
    except Exception as e:
        print(f"  ⚠️ 管道执行失败: {e}")


def demo_parallel():
    """演示 3：并行分析 — 多角度同时分析"""
    print("\n" + "=" * 60)
    print("  📋 演示 3：并行分析 — 多角度聚合")
    print("=" * 60)

    try:
        orchestrator = AgentOrchestrator()
        task = "AI Agent 技术在企业中的应用前景"

        print(f"\n  🎯 任务: {task}")
        results = orchestrator.execute_workflow("parallel_analysis", task)

        print(f"\n  📊 并行分析结果：")
        for step_name, result in results.items():
            print(f"  [{step_name}]: {str(result)[:200]}...")
    except Exception as e:
        print(f"  ⚠️ 并行分析失败: {e}")


def demo_self_improve():
    """演示 4：自改进循环"""
    print("\n" + "=" * 60)
    print("  📋 演示 4：自改进循环 — 撰写→审阅→改进")
    print("=" * 60)

    try:
        orchestrator = AgentOrchestrator()
        task = "写一段关于 Python 装饰器的简介（50字左右）"

        print(f"\n  🎯 任务: {task}")
        results = orchestrator.execute_workflow("self_improve", task)

        print(f"\n  📊 改进结果：")
        for step_name, result in results.items():
            print(f"  [{step_name}]: {str(result)[:200]}...")
    except Exception as e:
        print(f"  ⚠️ 自改进循环失败: {e}")


def demo_workflow_visualization():
    """演示 5：工作流可视化"""
    print("\n" + "=" * 60)
    print("  📋 演示 5：工作流结构可视化")
    print("=" * 60)

    def dummy_func(x):
        return x

    # 展示不同工作流的结构
    wf1 = AgentWorkflow("简单管道")
    wf1.add_step(WorkflowStep("输入", dummy_func))
    wf1.add_step(WorkflowStep("处理", dummy_func))
    wf1.add_step(WorkflowStep("输出", dummy_func))

    print("\n  简单管道：")
    print(wf1.visualize())

    wf2 = AgentWorkflow("条件路由")
    wf2.add_step(WorkflowStep("分类器", dummy_func))
    wf2.add_step(WorkflowStep("处理器A", dummy_func))
    wf2.add_step(WorkflowStep("处理器B", dummy_func))

    print("\n  条件路由：")
    print(wf2.visualize())

    print("""
  💡 编排模式总结：
  ┌─────────────────┬──────────────────────┬──────────────────────┐
  │    模式          │      适用场景          │      核心优势          │
  ├─────────────────┼──────────────────────┼──────────────────────┤
  │ 条件路由         │ 不同类型任务分派        │ 灵活性高，可扩展       │
  │ Agent 管道       │ 有依赖的串行处理        │ 流程清晰，可追踪       │
  │ 并行聚合         │ 无依赖的多视角分析      │ 效率高，视角全面       │
  │ 自改进循环       │ 追求质量的生成任务      │ 自动迭代，提高质量     │
  └─────────────────┴──────────────────────┴──────────────────────┘
    """)


def main():
    """主函数"""
    print("=" * 60)
    print("  Day 14: Agent 编排系统")
    print("  条件路由 | 管道 | 并行 | 自改进")
    print("=" * 60)
    print("  ⚡ 零 LangGraph 依赖 — 纯 Python 实现")
    print("=" * 60)

    try:
        demo_workflow_visualization()
        demo_conditional_routing()
        demo_pipeline()
        demo_parallel()
        demo_self_improve()

        print("\n" + "=" * 60)
        print("  ✅ 所有演示完成！")
        print("=" * 60)
        print("\n  💡 Day 14 关键要点：")
        print("    1. 工作流编排 — AgentWorkflow 实现步骤化的任务执行")
        print("    2. 条件路由 — LLM 分类器 + 路由表，实现智能分派")
        print("    3. Agent 管道 — 数据依次流经多个 Agent 处理")
        print("    4. 并行聚合 — 多 Agent 同时分析，LLM 汇总结果")
        print("    5. 自改进循环 — 撰写+审阅+改进，提升生成质量")
        print("\n  🔑 LangGraph 是可选方案，但核心编排模式用纯 Python 即可实现")

    except Exception as e:
        print(f"\n  ❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
