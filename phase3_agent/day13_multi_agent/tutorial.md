# Day 13: 多 Agent 协作系统

> 🎯 **学习目标**
>
> - 理解为什么需要多个 Agent 协作（单一 Agent 的局限性）
> - 掌握四种协作模式：顺序、并行、投票、管理者-工作者
> - 掌握 Agent 间的三种通信机制：点对点消息、共享黑板、发布订阅
> - 能根据任务复杂度选择合适的协作架构
> - 理解 SpecialistAgent 和 ManagerAgent 的角色分工

---

## 📖 前一天知识回顾

昨天我们探索了三种高级 Agent 推理模式（Plan-Execute / ReWOO / Self-Ask）：
- ✅ 单个 Agent 就能完成复杂的多步骤任务
- ✅ 不同模式适合不同场景

**但是，如果一个任务需要同时具备搜索、编码、数据分析三种能力呢？** 单个 Agent 的上下文窗口有限，system prompt 塞太多技能会导致专注度下降。这时候就需要**多 Agent 协作**。

---

## 📚 新知识讲解

### 1. 为什么需要多 Agent？

**比喻**：就像软件开发团队：
- 一个人可以写个小脚本（单 Agent）
- 但要做一个产品，需要产品经理 + 设计师 + 前端 + 后端 + 测试（多 Agent）

单 Agent 的局限性：
- 上下文窗口有限（塞不下所有工具和知识）
- 专注度下降（system prompt 太长会影响质量）
- 无法并行执行独立任务

### 2. BaseAgent 和 SpecialistAgent

所有 Agent 的基类是 `BaseAgent`（见 [agent_core.py](agent_core.py)），它提供了：
- LLM 客户端初始化
- Tool Calling Loop（`execute()` 方法）
- 工具注册和管理

`SpecialistAgent` 继承 `BaseAgent`，每个实例有独特的：
- **System Prompt**：定义专业领域
- **工具子集**：只分配相关工具（`get_agent_tools(["search"])`）

```python
researcher = SpecialistAgent(name="Researcher", specialty="信息搜索", tools=get_agent_tools(["search"]))
coder = SpecialistAgent(name="Coder", specialty="代码分析", tools=get_agent_tools(["code_analysis"]))
```

### 3. 四种协作模式

#### 3.1 顺序协作（SequentialCoordinator）

```
Agent A → Agent B → Agent C
(搜索)    (分析)    (报告)
```

每个 Agent 完成自己的任务后，结果传递给下游。适合有依赖关系的任务链。

#### 3.2 并行协作（ParallelCoordinator）

```
         ┌── Agent A (搜索主题A) ──┐
Task ────┼── Agent B (搜索主题B) ──┼──▶ 汇总结果
         └── Agent C (搜索主题C) ──┘
```

使用 `asyncio.gather` 实现真正的并行执行，适合无依赖关系的独立子任务。

#### 3.3 投票决策（VotingCoordinator）

```
问题: AI Agent 最大的应用价值是什么？

技术专家: "提升企业运营效率..."
产品专家: "实现智能化决策支持..."    ──▶ 投票: "提升效率"(2/3)
用户代表: "提升企业运营效率..."
```

多个 Agent 从不同角度回答同一个问题，`Counter` 投票选出多数答案。

#### 3.4 管理者-工作者（ManagerAgent）

```
Manager: 分解任务
  ├── Worker A: 搜索相关数据
  ├── Worker B: 分析数据趋势
  └── Worker C: 撰写最终报告
       └── Manager: 综合各 Worker 输出
```

Manager 用 LLM 自动分解任务（`decompose_task()`），分派给对应 Worker，最后汇总（`synthesize()`）。

### 4. 通信机制

见 [communication.py](communication.py)：

| 机制 | 类比 | 适用场景 |
|------|------|---------|
| **DirectMessenger** | 私聊/邮件 | Agent 间点对点通信 |
| **SharedBlackboard** | 共享白板 | 多个 Agent 读写共享数据 |
| **PubSubSystem** | 群通知 | 事件驱动的松耦合通信 |

---

## 💡 实例演示

### 实例1：顺序协作 — 专家流水线

```python
from coordinator import SequentialCoordinator

researcher = SpecialistAgent(name="Researcher", specialty="搜索", tools=get_agent_tools(["search"]))
coder = SpecialistAgent(name="Coder", specialty="代码", tools=get_agent_tools(["code_analysis"]))
analyst = SpecialistAgent(name="Analyst", specialty="数据", tools=get_agent_tools(["data_analysis"]))

coordinator = SequentialCoordinator([researcher, coder, analyst])
results = coordinator.execute([
    "搜索 Python AI 趋势",
    "分析代码: def hello(): ...",
    "分析数据: 12,45,78,23,56",
])
```

### 实例2：投票决策

```python
from coordinator import VotingCoordinator

voters = [
    SpecialistAgent(name="技术专家", ...),
    SpecialistAgent(name="产品专家", ...),
    SpecialistAgent(name="用户代表", ...),
]
coordinator = VotingCoordinator(voters)
winner, votes = coordinator.execute_voting("AI Agent 技术最大应用价值？")
```

### 实例3：发布订阅通信

```python
from communication import PubSubSystem
pubsub = PubSubSystem()
pubsub.subscribe("research.done", lambda msg: print(f"[通知] {msg}"))
pubsub.publish("research.done", "研究阶段完成")
```

完整演示见 [example.py](example.py)。

---

## ✍️ 练习题

### 练习1：基础题
1. 运行 `python example.py`，观察顺序执行和并行执行的时间差异
2. 修改 `demo_voting()` 中的投票者数量，测试平票情况
3. 使用 SharedBlackboard 在不同 Agent 间共享数据

### 练习2：进阶题
1. 实现"加权投票"：不同专家有不同的投票权重（如技术专家 2 票，用户代表 1 票）
2. 给 ManagerAgent 添加任务执行超时机制（Worker 超时则跳过）
3. 实现 Agent 间的"握手协议"：Worker 完成任务后向 Manager 发送确认消息

### 练习3：挑战题
1. 实现一个"Agent 市场"系统：Agent 可以动态加入/退出团队，Manager 根据可用 Agent 重新分配任务
2. 实现多 Agent 的"辩论模式"：两个 Agent 互相质疑对方的结论，第三个 Agent 仲裁

---

## 🔮 后一天知识展望

多 Agent 可以自由协作了，但面对复杂的工作流怎么办？明天我们学习 **Agent 编排**（Day14）——用工作流（Workflow）、管道（Pipeline）、条件路由（Router）来组织 Agent，让协作更加有序和可靠。**零 LangGraph 依赖，纯 Python 实现！**

---

## 📝 今日总结

- ✅ 多 Agent 协作 = 把大任务分解给专业 Agent 各司其职
- ✅ 顺序协作适合有依赖的任务链，并行协作适合独立子任务
- ✅ 投票决策从多角度评估同一问题，管理者-工作者自动分解复杂任务
- ✅ 三种通信机制覆盖不同耦合度需求：私聊/黑板/发布订阅
- ✅ 所有 Agent 和协调器使用原生 openai SDK，零框架依赖

---

## 🚀 下一步

1. 完成所有练习题
2. 思考：你工作中的哪个流程最适合多 Agent 协作？
3. 尝试将 Day12 的一种高级模式（如 Plan-Execute）作为多 Agent 系统的一个 Worker

---

## 📖 参考资料

- [Multi-Agent Systems: A Survey](https://arxiv.org/abs/1901.04887)
- [AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation](https://arxiv.org/abs/2308.08155)
- [ChatDev: Communicative Agents for Software Development](https://arxiv.org/abs/2307.07924)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
