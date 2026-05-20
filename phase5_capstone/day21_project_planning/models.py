"""
models.py — Day 21 数据模型：项目规划相关数据结构

定义项目规划各阶段的数据模型：
- Requirement: 功能/非功能需求
- TechnologyOption: 技术选型候选方案
- ArchitectureModule: 系统架构模块
- RiskItem: 风险项
- ProjectPlan: 完整项目计划（聚合以上所有）
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Requirement:
    """项目需求 — 单个功能或非功能需求

    示例:
        Requirement(id="REQ-01", name="用户登录", description="支持邮箱+密码登录",
                    priority="高", category="功能需求")
    """
    id: str                              # 需求编号（如 REQ-01）
    name: str                            # 需求名称（简短描述）
    description: str                     # 需求详细描述
    priority: str = "中"                 # 优先级：高/中/低
    category: str = "功能需求"           # 类别：功能需求/非功能需求/技术约束
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他需求 ID
    acceptance_criteria: List[str] = field(default_factory=list)  # 验收标准


@dataclass
class TechnologyOption:
    """技术选型方案 — 候选技术的多维度评估

    示例:
        TechnologyOption(name="FastAPI", category="后端框架",
                        pros=["高性能", "自动文档"], cons=["学习曲线"],
                        maturity="成熟", community="活跃")
    """
    name: str                            # 技术名称
    category: str                        # 技术类别（如"后端框架"、"数据库"）
    pros: List[str] = field(default_factory=list)    # 优势列表
    cons: List[str] = field(default_factory=list)    # 劣势列表
    score: float = 0.0                   # 综合评分（0-10）
    maturity: str = "成熟"               # 成熟度：成熟/成长/实验
    community: str = "活跃"             # 社区活跃度：活跃/一般/低迷
    learning_curve: str = "中等"         # 学习曲线：平缓/中等/陡峭
    license_type: str = "开源"           # 许可证类型


@dataclass
class ArchitectureModule:
    """架构模块 — 系统的一个功能单元

    示例:
        ArchitectureModule(name="用户服务", responsibility="处理用户注册、登录、权限管理",
                          dependencies=["数据库服务"], interfaces=["POST /api/login"])
    """
    name: str                            # 模块名称
    responsibility: str                  # 模块职责（一段话描述）
    dependencies: List[str] = field(default_factory=list)   # 依赖的其他模块
    interfaces: List[str] = field(default_factory=list)     # 对外接口（API/消息）
    tech_stack: List[str] = field(default_factory=list)     # 技术栈
    deployment: str = "容器化"           # 部署方式


@dataclass
class RiskItem:
    """风险项 — 项目潜在风险及缓解措施

    风险评估 = 概率 × 影响（两者都 0-1，乘积越高越需关注）
    """
    id: str                              # 风险编号
    description: str                     # 风险描述
    probability: float = 0.0             # 发生概率（0-1）
    impact: float = 0.0                  # 影响程度（0-1）
    mitigation: str = ""                 # 缓解措施
    category: str = "技术风险"           # 风险类别：技术/进度/资源/外部

    @property
    def risk_score(self) -> float:
        """风险评分 = 概率 × 影响"""
        return round(self.probability * self.impact, 4)


@dataclass
class ProjectPlan:
    """项目计划 — 聚合所有规划信息的完整计划书

    由 ProjectPlanner.generate_plan() 一站式生成
    """
    project_name: str                    # 项目名称
    project_description: str             # 项目概述
    requirements: List[Requirement] = field(default_factory=list)  # 需求列表
    tech_stack: List[TechnologyOption] = field(default_factory=list)  # 技术选型
    architecture: List[ArchitectureModule] = field(default_factory=list)  # 架构模块
    risks: List[RiskItem] = field(default_factory=list)  # 风险清单
    timeline: List[str] = field(default_factory=list)     # 里程碑时间线
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
