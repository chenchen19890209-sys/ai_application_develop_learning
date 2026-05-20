"""
planner.py — Day 21 核心：项目规划器（ProjectPlanner）

功能：
1. 需求分析 — LLM 驱动的需求分解（json_object 模式）
2. 技术选型 — 多维度评分评估矩阵
3. 架构设计 — LLM 驱动的系统架构设计
4. 风险评估 — 概率×影响矩阵分析
5. 完整计划 — 一站式生成 ProjectPlan

设计原则：零 LangChain 依赖，全部使用原生 openai SDK
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

import json
from typing import List, Optional
from openai import OpenAI
from models import Requirement, TechnologyOption, ArchitectureModule, RiskItem, ProjectPlan


class ProjectPlanner:
    """项目规划器 — LLM 驱动的项目规划辅助工具

    工作流程：
    需求描述 → 需求分析 → 技术选型 → 架构设计 → 风险评估 → 完整计划

    每个阶段都使用 LLM 来辅助分析和决策，
    但最终由人工审核和调整（LLM 是辅助，不是替代）。
    """

    def __init__(self):
        """初始化规划器 — 创建 LLM 客户端"""
        # 使用 OpenAI 兼容接口初始化 LLM 客户端
        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        self.model = OPENAI_MODEL

    def analyze_requirements(self, project_description: str) -> List[Requirement]:
        """需求分析 — LLM 将项目描述分解为结构化的需求列表

        使用 json_object 模式强制 LLM 返回结构化 JSON，
        包含功能需求和非功能需求的完整分解。

        Args:
            project_description: 项目的自然语言描述

        Returns:
            结构化的 Requirement 列表
        """
        prompt = f"""你是一个资深的软件项目需求分析师。请对以下项目进行需求分析，
将项目描述分解为详细的功能需求和非功能需求。

项目描述：
{project_description}

请以 JSON 格式返回，包含以下字段：
- functional: 功能需求列表（每项包含 id, name, description, priority, acceptance_criteria）
- non_functional: 非功能需求列表（每项包含 id, name, description, priority）

要求：
1. 每个需求必须有唯一的 ID（如 REQ-01, NFR-01）
2. 优先级分为"高"、"中"、"低"三级
3. 功能需求最多 8 条，非功能需求最多 4 条
4. 功能需求的 acceptance_criteria 是验收标准列表"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},  # 强制 JSON 输出
            temperature=0.3,
        )

        # 解析 LLM 返回的 JSON
        raw = response.choices[0].message.content
        data = json.loads(raw)

        # 转换为 Requirement 对象列表
        requirements = []
        for item in data.get("functional", []):
            requirements.append(Requirement(
                id=item.get("id", ""),
                name=item.get("name", ""),
                description=item.get("description", ""),
                priority=item.get("priority", "中"),
                category="功能需求",
                acceptance_criteria=item.get("acceptance_criteria", []),
            ))
        for item in data.get("non_functional", []):
            requirements.append(Requirement(
                id=item.get("id", ""),
                name=item.get("name", ""),
                description=item.get("description", ""),
                priority=item.get("priority", "中"),
                category="非功能需求",
            ))

        print(f"  ✅ 需求分析完成: {len(requirements)} 条需求"
              f"（功能:{len(data.get('functional',[]))} 非功能:{len(data.get('non_functional',[]))}）")
        return requirements

    def evaluate_technology(self, requirement_name: str,
                           candidates: List[str]) -> List[TechnologyOption]:
        """技术选型评估 — 对候选技术进行多维度评分

        评估维度：功能性、性能、成熟度、社区支持、学习成本、许可合规

        Args:
            requirement_name: 待满足的需求名称
            candidates: 候选技术列表

        Returns:
            带评分的 TechnologyOption 列表
        """
        prompt = f"""你是一个技术选型顾问。请对以下候选技术进行评估。

需求场景：{requirement_name}
候选技术：{", ".join(candidates)}

请对每个候选技术从以下维度打分（每项 0-10 分）并给出综合评价：
1. 功能匹配度：是否满足需求
2. 性能表现：在高负载下的表现
3. 成熟度：是否经过大规模生产验证
4. 社区活跃度：GitHub stars、issue 响应速度
5. 学习成本：团队成员上手难度（分数越高表示越容易）
6. 许可合规：开源许可的友好程度

以 JSON 格式返回：
{{"evaluations": [{{"name": "...", "scores": {{...}}, "pros": [...], "cons": [...], "overall_score": 7.5}}]}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)

        # 转换为 TechnologyOption 对象
        options = []
        for item in data.get("evaluations", []):
            options.append(TechnologyOption(
                name=item.get("name", ""),
                category=requirement_name,
                pros=item.get("pros", []),
                cons=item.get("cons", []),
                score=item.get("overall_score", 0.0),
            ))

        print(f"  ✅ 技术选型完成: 评估了 {len(options)} 个候选方案")
        for opt in options:
            print(f"    {opt.name}: {opt.score}/10")
        return options

    def design_architecture(self, requirements: List[Requirement]) -> List[ArchitectureModule]:
        """架构设计 — LLM 根据需求设计系统模块结构

        设计原则：高内聚低耦合、单一职责、接口清晰

        Args:
            requirements: 需求列表

        Returns:
            架构模块列表（含依赖关系和接口定义）
        """
        # 构建需求摘要
        req_summary = "\n".join([
            f"- [{r.id}] {r.name}: {r.description[:80]}（优先级:{r.priority}）"
            for r in requirements
        ])

        prompt = f"""你是一个系统架构师。请根据以下需求设计系统架构。

项目需求：
{req_summary}

请设计系统的模块结构，遵循以下原则：
- 高内聚低耦合：每个模块职责单一，模块间依赖最少
- 接口清晰：每个模块定义明确的对外接口
- 可扩展：架构应支持未来新增功能

以 JSON 格式返回：
{{"modules": [{{"name": "...", "responsibility": "...", "dependencies": [...], "interfaces": [...], "tech_suggestion": "..."}}]}}

要求：模块数 4-6 个，每个模块有明确的职责边界。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)

        # 转换为 ArchitectureModule 对象
        modules = []
        for item in data.get("modules", []):
            modules.append(ArchitectureModule(
                name=item.get("name", ""),
                responsibility=item.get("responsibility", ""),
                dependencies=item.get("dependencies", []),
                interfaces=item.get("interfaces", []),
                tech_stack=[item.get("tech_suggestion", "")] if item.get("tech_suggestion") else [],
            ))

        print(f"  ✅ 架构设计完成: {len(modules)} 个模块")
        return modules

    def assess_risks(self, requirements: List[Requirement],
                    modules: List[ArchitectureModule]) -> List[RiskItem]:
        """风险评估 — LLM 分析项目的潜在风险和缓解措施

        使用 概率×影响 矩阵评估每个风险的重要程度

        Args:
            requirements: 需求列表
            modules: 架构模块列表

        Returns:
            风险评估清单
        """
        # 构建上下文摘要
        context = "需求模块:\n" + "\n".join([f"- {m.name}: {m.responsibility[:60]}" for m in modules])
        context += "\n\n关键需求:\n" + "\n".join([
            f"- {r.name}" for r in requirements if r.priority == "高"
        ])

        prompt = f"""你是一个项目风险管理专家。请根据以下项目信息进行风险评估。

{context}

请从以下四个维度识别潜在风险：
1. 技术风险：技术选型、架构设计、性能瓶颈
2. 进度风险：工期安排、资源冲突
3. 资源风险：人力、硬件、预算
4. 外部风险：第三方依赖、政策变化

对每个风险给出：
- 发生概率（0-1）
- 影响程度（0-1）
- 具体可行的缓解措施

以 JSON 格式返回：
{{"risks": [{{"id": "RSK-01", "description": "...", "probability": 0.6, "impact": 0.8, "mitigation": "...", "category": "技术风险"}}]}}

要求：每个维度至少识别 1 个风险，总共 4-6 条。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)

        # 转换为 RiskItem 对象
        risks = []
        for item in data.get("risks", []):
            risks.append(RiskItem(
                id=item.get("id", ""),
                description=item.get("description", ""),
                probability=item.get("probability", 0.0),
                impact=item.get("impact", 0.0),
                mitigation=item.get("mitigation", ""),
                category=item.get("category", "技术风险"),
            ))

        # 按风险评分降序排列
        risks.sort(key=lambda r: r.risk_score, reverse=True)

        print(f"  ✅ 风险评估完成: {len(risks)} 项风险")
        for risk in risks:
            level = "🔴" if risk.risk_score > 0.5 else ("🟡" if risk.risk_score > 0.2 else "🟢")
            print(f"    {level} {risk.id}: {risk.description[:50]}... (评分:{risk.risk_score})")
        return risks

    def generate_timeline(self, requirements: List[Requirement],
                         modules: List[ArchitectureModule]) -> List[str]:
        """生成项目时间线 — 根据需求和模块估算里程碑

        Args:
            requirements: 需求列表
            modules: 架构模块列表

        Returns:
            按时间排列的里程碑列表
        """
        prompt = f"""你是一个项目经理。请根据以下信息制定项目里程碑时间线。

模块数：{len(modules)} 个
需求数：{len(requirements)} 条（其中 {sum(1 for r in requirements if r.priority == '高')} 条高优先级）

请制定一个 4-6 个阶段的里程碑计划。以 JSON 数组格式返回：
["阶段1: ... (预计第1-2周)", "阶段2: ... (预计第3-4周)", ...]"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)

        # 处理可能的返回格式：数组 或 包含 milestones 字段的对象
        if isinstance(data, list):
            timeline = data
        else:
            timeline = data.get("milestones", data.get("timeline", []))

        print(f"  ✅ 时间线规划完成: {len(timeline)} 个里程碑")
        return timeline

    def generate_plan(self, project_name: str,
                     project_description: str) -> ProjectPlan:
        """一站式生成完整项目计划

        依次执行：需求分析 → 技术选型 → 架构设计 → 风险评估 → 时间线

        Args:
            project_name: 项目名称
            project_description: 项目自然语言描述

        Returns:
            完整的 ProjectPlan 对象
        """
        print(f"\n{'='*60}")
        print(f"  项目规划: {project_name}")
        print(f"{'='*60}")
        print(f"  描述: {project_description}")

        # 阶段 1：需求分析
        print(f"\n  [阶段 1/5] 需求分析...")
        requirements = self.analyze_requirements(project_description)

        # 阶段 2：技术选型（基于第一个高优先级需求做示范）
        print(f"\n  [阶段 2/5] 技术选型...")
        high_priority = [r for r in requirements if r.priority == "高"]
        tech_needs = [r.name for r in high_priority[:2]] if high_priority else ["后端框架"]
        tech_options = self.evaluate_technology(
            requirement_name="后端技术栈",
            candidates=["FastAPI", "Flask", "Django", "Spring Boot"]
        )

        # 阶段 3：架构设计
        print(f"\n  [阶段 3/5] 架构设计...")
        modules = self.design_architecture(requirements)

        # 阶段 4：风险评估
        print(f"\n  [阶段 4/5] 风险评估...")
        risks = self.assess_risks(requirements, modules)

        # 阶段 5：时间线规划
        print(f"\n  [阶段 5/5] 时间线规划...")
        timeline = self.generate_timeline(requirements, modules)

        # 组装完整的项目计划
        plan = ProjectPlan(
            project_name=project_name,
            project_description=project_description,
            requirements=requirements,
            tech_stack=tech_options,
            architecture=modules,
            risks=risks,
            timeline=timeline,
        )

        print(f"\n  🎉 项目计划生成完成!")
        self._print_summary(plan)
        return plan

    def _print_summary(self, plan: ProjectPlan):
        """打印项目计划摘要"""
        print(f"\n{'='*60}")
        print(f"  📋 项目计划摘要: {plan.project_name}")
        print(f"{'='*60}")
        print(f"  需求数: {len(plan.requirements)}（功能:{sum(1 for r in plan.requirements if r.category=='功能需求')} 非功能:{sum(1 for r in plan.requirements if r.category=='非功能需求')}）")
        print(f"  技术评估: {len(plan.tech_stack)} 项候选方案")
        print(f"  架构模块: {len(plan.architecture)} 个")
        print(f"  风险项: {len(plan.risks)} 条")
        print(f"  里程碑: {len(plan.timeline)} 个")

        if plan.risks:
            high_risks = [r for r in plan.risks if r.risk_score > 0.5]
            print(f"  ⚠️  高风险项: {len(high_risks)} 条（需重点关注）")


def main():
    """独立测试 — 运行项目规划器"""
    planner = ProjectPlanner()

    # 测试用项目描述
    test_project = "构建一个面向中小企业的智能客服系统，支持文本对话和知识库检索"

    try:
        plan = planner.generate_plan(
            project_name="智能客服系统",
            project_description=test_project,
        )

        print(f"\n  📊 完整计划已生成（{len(plan.requirements)}需求, "
              f"{len(plan.architecture)}模块, {len(plan.risks)}风险）")

    except Exception as e:
        print(f"\n  ⚠️ LLM 调用失败: {e}")
        print(f"  💡 需要配置有效的 OPENAI_API_KEY")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
