# Day 21: 项目规划与架构设计

> 🎯 **学习目标**
>
> - 掌握 AI 应用项目的完整规划流程：需求→选型→架构→风险→时间线
> - 学习用 LLM 辅助需求分解（`response_format={"type": "json_object"}`）
> - 掌握多维度技术选型评估矩阵
> - 理解系统架构设计的关键原则：高内聚低耦合、接口清晰
> - 掌握风险管理的 概率×影响 评估方法

---

## 📖 Phase 4 回顾

Phase 4（Day16-20）我们走完了 RAG 的完整链路：
- ✅ Day16: RAG 原理 + Embedding + ChromaDB
- ✅ Day17: 文档加载 + 分块策略 + RAGBuilder
- ✅ Day18: 混合检索 + RRF 融合 + 重排序
- ✅ Day19: 评估体系 + 多轮对话 RAG
- ✅ Day20: 生产级 RAG 系统

**今天，Phase 5 综合实战正式开始！** 我们将用 3 天时间，把 Agent（Phase 3）和 RAG（Phase 4）融合为一个完整的 AI 应用产品。

**第一步：好的项目始于好的规划。**

---

## 📚 新知识讲解

### 1. 项目规划的 5 个阶段

**比喻**：项目规划就像建筑设计——先画蓝图，再施工。

```
需求分析 ──▶ 技术选型 ──▶ 架构设计 ──▶ 风险评估 ──▶ 时间线
   │              │             │             │            │
   │              │             │             │            │
"要做什么"    "用什么做"    "怎么组织"    "会出什么问题"  "什么时候完成"
```

### 2. 需求分析 — LLM 驱动

见 [planner.py](planner.py) 的 `analyze_requirements()`：

```python
def analyze_requirements(self, project_description: str) -> List[Requirement]:
    # 使用 response_format={"type": "json_object"} 确保 LLM 返回结构化 JSON
    # 自动分解为功能需求和非功能需求
```

**功能需求 vs 非功能需求：**
- 功能需求：系统"做什么"（如：用户登录、知识检索、对话管理）
- 非功能需求：系统"怎么做"（如：1000 并发、99.9% 可用性、响应<200ms）

### 3. 技术选型 — 多维度评估矩阵

见 [planner.py](planner.py) 的 `evaluate_technology()`：

| 评估维度 | 权重 | 说明 |
|---------|------|------|
| 功能匹配度 | ⭐⭐⭐ | 是否满足核心需求 |
| 性能表现 | ⭐⭐⭐ | 高负载下的表现 |
| 成熟度 | ⭐⭐ | 生产验证案例 |
| 社区活跃度 | ⭐⭐ | 遇到问题能否快速解决 |
| 学习成本 | ⭐ | 团队上手难度 |
| 许可合规 | ⭐ | 商业使用友好度 |

### 4. 架构设计 — 模块化思维

见 [planner.py](planner.py) 的 `design_architecture()`：

原则：
- **高内聚低耦合**：每个模块职责单一
- **接口清晰**：模块间通过 API/消息通信
- **可扩展**：新增功能不需大改现有模块

### 5. 风险评估 — 概率×影响矩阵

见 [planner.py](planner.py) 的 `assess_risks()`：

```
风险评分 = 发生概率 × 影响程度

🔴 高风险（>0.50） — 必须制定详细缓解计划
🟡 中风险（0.20-0.50） — 需要监控和备选方案
🟢 低风险（<0.20） — 接受或简单应对
```

四个风险维度：技术风险、进度风险、资源风险、外部风险。

### 6. 数据模型

见 [models.py](models.py) — 5 个核心数据类：

```python
Requirement      # 需求（id, name, description, priority, acceptance_criteria）
TechnologyOption # 技术选型（name, pros, cons, score）
ArchitectureModule # 架构模块（name, responsibility, dependencies, interfaces）
RiskItem         # 风险项（description, probability, impact, mitigation）
ProjectPlan      # 聚合以上所有 + 时间线
```

---

## 💡 实例演示

### 实例1：需求分析

```python
from planner import ProjectPlanner
planner = ProjectPlanner()
requirements = planner.analyze_requirements(
    "构建智能客服系统，支持文本对话和知识库检索..."
)
# LLM 自动分解为 ~10 条结构化需求（功能 + 非功能）
```

### 实例2：技术选型

```python
options = planner.evaluate_technology(
    requirement_name="后端 API 框架",
    candidates=["FastAPI", "Flask", "Django", "Spring Boot"],
)
# 每个候选方案从 6 个维度评分，输出综合分数
```

### 实例3：完整计划

```python
plan = planner.generate_plan(
    project_name="智能客服系统",
    project_description="面向中小企业的智能客服系统...",
)
# 一站式：需求分析 → 技术选型 → 架构设计 → 风险评估 → 时间线
```

**运行方法：**
```bash
cd phase5_capstone/day21_project_planning
python example.py
```

---

## ✍️ 练习题

### 练习1：基础题
1. 运行 `python example.py`，观察 5 个演示的输出
2. 修改 `demo_technology()` 中的候选技术列表，添加 `Sanic` 和 `Tornado`
3. 查看 `models.py`，理解每个数据类的字段含义

### 练习2：进阶题
1. 给 `evaluate_technology()` 添加自定义权重：不同项目可以有不同的维度权重
2. 实现 `compare_architectures()`：对同一组需求生成 2 套架构方案并对比
3. 给 `ProjectPlan` 添加 `to_markdown()` 方法：将计划导出为 Markdown 文档

### 练习3：挑战题
1. 实现"增量规划"：项目需求变更后，只重新分析受影响的部分
2. 构建一个"规划对比工具"：同时生成传统方法和 AI-native 方法的两套规划方案

---

## 🔮 后一天知识展望

有了项目规划蓝图，明天（Day22）我们进入 **RAG + Agent 融合**——这是整个课程的精华！我们将 Phase 3 的 Agent 和 Phase 4 的 RAG 融合为一个系统，Agent 作为核心调度器，RAG 作为知识检索工具。**零 LangChain，纯原生实现！**

---

## 📝 今日总结

- ✅ 项目规划 5 阶段：需求→选型→架构→风险→时间线
- ✅ LLM 驱动的需求分解（json_object 模式确保结构化输出）
- ✅ 技术选型 = 多维度评估（6 维度 × 候选方案）
- ✅ 架构设计 = 模块化 + 依赖关系 + 接口定义
- ✅ 风险评估 = 概率 × 影响（4 维度覆盖）
- ✅ ProjectPlanner 将所有阶段整合为一站式工作流

---

## 🚀 下一步

1. 完成所有练习题
2. 用 ProjectPlanner 规划你自己的项目
3. 思考：LLM 在规划中应该扮演什么角色？（辅助 vs 替代）

---

## 📖 参考资料

- [Software Architecture in Practice (Bass, Clements, Kazman)](https://www.oreilly.com/library/view/software-architecture-in/9780136885979/)
- [12-Factor App 方法论](https://12factor.net/)
- [Risk Matrix (Wikipedia)](https://en.wikipedia.org/wiki/Risk_matrix)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
