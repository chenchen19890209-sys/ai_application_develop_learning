"""
example.py — Day 21 完整演示：项目规划与架构设计

演示内容：
1. 需求分析 — LLM 将智能客服系统分解为结构化需求
2. 技术选型 — 多维度评估后端框架候选方案
3. 架构设计 — 根据需求设计系统模块结构
4. 风险评估 — 识别潜在风险并制定缓解措施
5. 完整计划 — 一站式生成 ProjectPlan
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models import Requirement, TechnologyOption, ArchitectureModule, RiskItem, ProjectPlan
from planner import ProjectPlanner


def demo_requirements():
    """演示 1：需求分析"""
    print("\n" + "=" * 60)
    print("  演示 1：需求分析 — 智能客服系统")
    print("=" * 60)

    planner = ProjectPlanner()

    project_desc = (
        "构建一个面向中小企业的智能客服系统。"
        "核心功能包括：文本对话（支持自然语言理解）、知识库检索（RAG）、"
        "多轮对话管理、人工客服转接、对话记录和分析报表。"
        "系统需要支持 1000 并发用户，SLA 要求 99.9% 可用性。"
    )

    try:
        requirements = planner.analyze_requirements(project_desc)
        print(f"\n  📋 共 {len(requirements)} 条需求：")
        for req in requirements:
            print(f"\n  [{req.id}] {req.name} (优先级:{req.priority}, 类别:{req.category})")
            print(f"    {req.description[:100]}...")
            if req.acceptance_criteria:
                print(f"    验收标准: {', '.join(req.acceptance_criteria[:2])}")
    except Exception as e:
        print(f"  ⚠️ LLM 调用失败: {e}")


def demo_technology():
    """演示 2：技术选型评估"""
    print("\n" + "=" * 60)
    print("  演示 2：技术选型 — 后端框架评估")
    print("=" * 60)

    planner = ProjectPlanner()

    try:
        options = planner.evaluate_technology(
            requirement_name="后端 API 框架（高并发、异步支持）",
            candidates=["FastAPI", "Flask", "Django REST", "Spring Boot"],
        )
        print(f"\n  📊 评估结果：")
        for opt in options:
            print(f"\n  {opt.name}: {opt.score}/10")
            print(f"    优势: {', '.join(opt.pros[:3])}")
            if opt.cons:
                print(f"    劣势: {', '.join(opt.cons[:3])}")
    except Exception as e:
        print(f"  ⚠️ LLM 调用失败: {e}")


def demo_architecture():
    """演示 3：架构设计"""
    print("\n" + "=" * 60)
    print("  演示 3：架构设计 — 智能客服系统模块")
    print("=" * 60)

    planner = ProjectPlanner()

    # 手动构建几个示例需求
    sample_reqs = [
        Requirement(id="REQ-01", name="文本对话", description="支持自然语言多轮对话", priority="高"),
        Requirement(id="REQ-02", name="知识库检索", description="基于 RAG 的知识检索和回答", priority="高"),
        Requirement(id="REQ-03", name="人工转接", description="复杂问题自动转接人工客服", priority="中"),
        Requirement(id="REQ-04", name="对话分析", description="对话记录存储和分析报表", priority="中"),
        Requirement(id="NFR-01", name="高并发", description="支持 1000 并发用户", priority="高", category="非功能需求"),
        Requirement(id="NFR-02", name="高可用", description="99.9% SLA", priority="高", category="非功能需求"),
    ]

    try:
        modules = planner.design_architecture(sample_reqs)
        print(f"\n  📐 共 {len(modules)} 个架构模块：")
        for mod in modules:
            print(f"\n  📦 {mod.name}")
            print(f"    职责: {mod.responsibility[:120]}...")
            if mod.dependencies:
                print(f"    依赖: {', '.join(mod.dependencies)}")
            if mod.interfaces:
                print(f"    接口: {', '.join(mod.interfaces[:3])}")
    except Exception as e:
        print(f"  ⚠️ LLM 调用失败: {e}")


def demo_risks():
    """演示 4：风险评估"""
    print("\n" + "=" * 60)
    print("  演示 4：风险评估矩阵")
    print("=" * 60)

    planner = ProjectPlanner()

    # 构建示例需求和模块
    sample_reqs = [
        Requirement(id="REQ-01", name="文本对话", description="自然语言多轮对话", priority="高"),
        Requirement(id="REQ-02", name="知识库检索", description="RAG 检索增强生成", priority="高"),
    ]
    sample_modules = [
        ArchitectureModule(name="对话引擎", responsibility="NLU 理解和对话状态管理"),
        ArchitectureModule(name="知识库服务", responsibility="文档索引和语义检索"),
        ArchitectureModule(name="Web 网关", responsibility="请求路由和限流"),
    ]

    try:
        risks = planner.assess_risks(sample_reqs, sample_modules)
        print(f"\n  ⚠️  共 {len(risks)} 项风险（按严重程度排序）：")
        for risk in risks:
            level = "🔴 高危" if risk.risk_score > 0.5 else ("🟡 中危" if risk.risk_score > 0.2 else "🟢 低危")
            print(f"\n  {level} [{risk.id}] {risk.category}")
            print(f"    描述: {risk.description[:100]}...")
            print(f"    概率: {risk.probability:.0%}, 影响: {risk.impact:.0%}, 评分: {risk.risk_score}")
            print(f"    缓解: {risk.mitigation[:100]}...")
    except Exception as e:
        print(f"  ⚠️ LLM 调用失败: {e}")


def demo_full_plan():
    """演示 5：一站式完整计划"""
    print("\n" + "=" * 60)
    print("  演示 5：一站式项目计划生成")
    print("=" * 60)

    planner = ProjectPlanner()

    try:
        plan = planner.generate_plan(
            project_name="中小企业智能客服系统",
            project_description=(
                "面向中小企业的智能客服系统，具备文本对话、知识库检索（RAG）、"
                "多轮对话管理和人工客服转接功能。支持 1000 并发、99.9% 可用性。"
                "前端使用 React，后端 API 需支持高并发异步处理，数据存储需支持全文搜索。"
            ),
        )
        print(f"\n  📊 计划数据：")
        print(f"    需求: {len(plan.requirements)} 条")
        print(f"    技术评估: {len(plan.tech_stack)} 项")
        print(f"    架构模块: {len(plan.architecture)} 个")
        print(f"    风险: {len(plan.risks)} 条")
        print(f"    里程碑: {len(plan.timeline)} 个")
    except Exception as e:
        print(f"  ⚠️ LLM 调用失败: {e}")


def main():
    """主函数 — 运行所有演示"""
    print("=" * 60)
    print("  Day 21: 项目规划与架构设计")
    print("  需求分析 | 技术选型 | 架构设计 | 风险评估")
    print("=" * 60)

    try:
        demo_requirements()
        demo_technology()
        demo_architecture()
        demo_risks()
        demo_full_plan()

        print("\n" + "=" * 60)
        print("  ✅ Day 21 所有演示完成！")
        print("=" * 60)
        print("\n  💡 Day 21 关键要点：")
        print("    1. 需求分析 — LLM 辅助分解（json_object 模式）")
        print("    2. 技术选型 — 多维度评分（功能/性能/成熟度/社区/成本/合规）")
        print("    3. 架构设计 — 模块化 + 依赖关系 + 接口定义")
        print("    4. 风险评估 — 概率×影响矩阵，4 维度覆盖")
        print("    5. ProjectPlanner — 一站式从描述到完整计划")

    except Exception as e:
        print(f"\n  ❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
