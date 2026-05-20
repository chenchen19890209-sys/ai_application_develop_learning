# Day 14: Agent 编排系统 — 工作流 / 管道 / 条件路由

> 🎯 **学习目标**
>
> - 掌握 Agent 工作流编排的核心模式：步骤化执行、条件路由、管道
> - 理解如何用纯 Python 实现编排（零 LangGraph 依赖）
> - 掌握并行聚合模式：多 Agent 同时分析后汇总
> - 掌握自改进循环模式：撰写→审阅→改进
> - 了解 LangGraph 的定位：可选方案而非必需品

---

## 📖 前一天知识回顾

昨天我们实现了多 Agent 协作系统：
- ✅ 四种协作模式：顺序、并行、投票、管理者-工作者
- ✅ 三种通信机制：私聊、黑板、发布订阅

**问题：** Day13 的多 Agent 系统虽然能协作，但缺乏"流程管理"——无法定义条件分支、循环、错误恢复等高级控制流。如果任务需要"根据类型走不同处理流程"或"反复修改直到满意"，怎么办？

**今天，Agent 编排系统解决的就是这个问题！**

---

## 📚 新知识讲解

### 1. 什么是 Agent 编排？

**比喻**：多 Agent 协作（Day13）像是同事们自由讨论；Agent 编排（Day14）像是**公司的标准化流程（SOP）**——每个任务走哪个流程、遇到什么情况怎么处理，都有明确规定。

```
自由协作(Day13)          编排(Day14)
┌─A──B──C─┐              ┌──开始──┐
│ 随心所欲  │              │ 分类器  │
└──────────┘              ├──A流程──┤
                          ├──B流程──┤
                          └──结束──┘
```

### 2. 核心组件

见 [orchestration.py](orchestration.py)：

#### 2.1 WorkflowStep — 工作流步骤

```python
@dataclass
class WorkflowStep:
    name: str           # 步骤名称
    agent_func: Callable  # 要执行的函数
    task_template: str  # 任务模板（支持 {input} 占位符）
    condition: Optional[Callable] = None  # 条件判断函数
```

#### 2.2 AgentWorkflow — 工作流引擎

```
Step 1 ──▶ Step 2 ──▶ [条件路由] ──┬──▶ Step 3A
                                   └──▶ Step 3B
```

- `add_step()` — 添加步骤
- `add_router(from_step, condition, true_step, false_step)` — 添加条件分叉
- `run()` — 执行工作流
- `visualize()` — ASCII 流程图可视化

#### 2.3 AgentPipeline — 数据处理管道

```
输入 ──▶ Agent A ──▶ Agent B ──▶ Agent C ──▶ 输出
        (搜索)       (分析)       (报告)
```

数据依次流经每个 Agent，每个 Agent 的输出是下一个的输入。

### 3. ConditionalRouter — 条件路由

```
用户查询 ──▶ LLM 分类器（json_object 模式）──▶ 路由表
              │
              ├── "数学计算" → CalculatorAgent
              ├── "天气查询" → WeatherAgent
              ├── "知识问答" → SearchAgent
              └── "文本分析" → TextAnalysisAgent
```

核心代码：
```python
router = ConditionalRouter()
category = router.classify(query, categories=["数学计算","天气查询","知识问答"])
result = router.route(category, task)
```

### 4. 三种预设编排模式

`AgentOrchestrator` 提供了三种开箱即用的工作流：

| 模式 | 流程 | 适用场景 |
|------|------|---------|
| `research_pipeline` | 搜索→分析→报告 | 调研任务 |
| `parallel_analysis` | 多角度同时分析→汇总 | 需要多视角评估 |
| `self_improve` | 撰写→审阅→改进（循环） | 追求质量的生成任务 |

### 5. 与 LangGraph 的对比

| 维度 | 纯 Python 编排（本课程） | LangGraph |
|------|--------------------------|-----------|
| 学习曲线 | 低（标准 Python） | 中高（框架概念多） |
| 依赖 | 零额外依赖 | langgraph + langchain |
| 可视化 | ASCII 流程图 | 图结构可视化 |
| 状态管理 | 手动控制 | 自动状态图 |
| 适用场景 | 中小型工作流 | 复杂有状态工作流 |
| 生产就绪 | ✅ 直接可用 | ✅ 需要学习框架 |

**我们的立场**：核心编排模式用纯 Python 即可实现，LangGraph 是可选方案。

---

## 💡 实例演示

### 实例1：条件路由

```python
from orchestration import ConditionalRouter
router = ConditionalRouter()
queries = ["帮我算 12345*6789", "北京今天天气如何？", "什么是机器学习？"]
for q in queries:
    category = router.classify(q, ["数学计算", "天气查询", "知识问答", "文本分析"])
    print(f"{q} → {category}")
```

### 实例2：调研管道

```python
from orchestration import AgentOrchestrator
orchestrator = AgentOrchestrator()
results = orchestrator.execute_workflow("research_pipeline", "Python AI 应用")
# 自动执行：搜索 → 分析 → 报告
```

### 实例3：自改进循环

```python
results = orchestrator.execute_workflow("self_improve", "写 Python 装饰器简介（50字）")
# 撰写 → 审阅 → 改进 → 审阅 → ...（直到质量达标）
```

完整演示见 [example.py](example.py)。

---

## ✍️ 练习题

### 练习1：基础题
1. 运行 `python example.py`，观察所有 5 个演示
2. 修改条件路由的分类类别，添加"翻译任务"路由
3. 创建一个自定义的 3 步工作流并用 `visualize()` 打印流程图

### 练习2：进阶题
1. 给 AgentWorkflow 添加"步骤重试"：某步骤失败后自动重试最多 3 次
2. 实现"工作流嵌套"：一个工作流的某个步骤本身是另一个工作流
3. 为自改进循环添加"最大迭代次数"和"质量阈值"两个退出条件

### 练习3：挑战题
1. 实现一个"动态工作流生成器"：根据任务描述，由 LLM 自动生成对应的 Workflow
2. 实现工作流的"断点续传"功能：执行中断后可以从上次停止的步骤继续

---

## 🔮 后一天知识展望

编排能力就绪，但离生产环境还差关键一步。明天是 Phase 3 的最后一天——**Agent 生产化**（Day15）。我们将学习日志、缓存、重试、断路器、限流、验证、指标——这 7 大生产基础设施，让 Agent 从"能跑"变成"能扛"。

---

## 📝 今日总结

- ✅ WorkflowStep + AgentWorkflow：用纯 Python 实现步骤化任务编排
- ✅ ConditionalRouter：LLM 分类 + 路由表，智能分派不同任务
- ✅ AgentPipeline：数据依次流经多个 Agent，管道式处理
- ✅ 三种预设模式覆盖常见场景：调研管道/并行分析/自改进循环
- ✅ 零 LangGraph 依赖——核心编排模式与框架无关
- ✅ LangGraph 是可选方案，不是必需品

---

## 🚀 下一步

1. 完成所有练习题
2. 思考：你的项目中哪些流程适合编排成工作流？
3. 阅读 LangGraph 文档了解其定位（作为可选知识拓展）

---

## 📖 参考资料

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)（可选了解）
- [Workflow Patterns](http://www.workflowpatterns.com/)（通用工作流模式）
- [Building Effective Agents (Anthropic)](https://www.anthropic.com/engineering/building-effective-agents)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
