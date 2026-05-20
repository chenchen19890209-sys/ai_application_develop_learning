# Day 12: 高级 Agent 模式 — Plan-Execute / ReWOO / Self-Ask

> 🎯 **学习目标**
>
> - 理解并实现三种超越 ReAct 的高级 Agent 推理模式
> - 掌握 Plan-Execute 模式：先规划后执行，适合结构化多步骤任务
> - 掌握 ReWOO 模式：占位符批量执行，减少 LLM 调用次数
> - 掌握 Self-Ask 模式：递归追问链，适合需要层层递进的复杂推理
> - 能根据任务特点选择最合适的 Agent 模式

---

## 📖 前一天知识回顾

昨天我们构建了完整的自定义工具和记忆系统：
- ✅ MCP-native 工具类（WeatherTool、CalculatorTool、TodoTool 等）
- ✅ 三级记忆架构（WorkingMemory → ShortTermMemory → LongTermMemory）
- ✅ MemoryAgent 将记忆与工具调用融合

**问题：** Day09 的 ReAct Agent 每走一步都要调用一次 LLM（Thought→Action→Observation），这在多步骤任务中效率很低。有没有更高效的推理模式？

**今天，我们探索三种高级 Agent 模式来回答这个问题！**

---

## 📚 新知识讲解

### 1. 为什么需要多种 Agent 模式？

**比喻**：不同的工作需要不同的工作方法：
- **盖房子** → 先画图纸（Plan），再按图施工（Execute）= Plan-Execute
- **点外卖** → 同时下单多道菜，等所有菜到齐再吃 = ReWOO
- **做研究** → 一个问题引出下一个问题，层层深入 = Self-Ask
- **日常对话** → 想到什么做什么，灵活应变 = ReAct（Day09）

### 2. Plan-Execute 模式

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  规划阶段  │────▶│   执行阶段     │────▶│   汇总阶段     │
│  (Plan)   │     │  (Execute)    │     │ (Synthesize)  │
│           │     │               │     │               │
│ LLM 生成  │     │ 逐步执行每个   │     │ LLM 综合所有   │
│ JSON 步骤  │     │ 步骤（tool    │     │ 步骤结果生成   │
│           │     │  calling）    │     │ 最终答案       │
└──────────┘     └──────────────┘     └──────────────┘
```

核心代码见 [plan_execute.py](plan_execute.py)：
- `plan()` — 用 `response_format={"type": "json_object"}` 让 LLM 生成结构化步骤
- `execute_step()` — 对每个步骤执行 tool calling loop
- `synthesize()` — 汇总所有步骤结果

### 3. ReWOO 模式（Reasoning WithOut Observation）

ReWOO 的核心创新：**用占位符批量执行，减少 LLM 调用次数**。

```
Plan: #E1 = search("深度学习")     ──┐
      #E2 = search("神经网络")     ──┤ 批量并行执行
      #E3 = calculate("100+200")   ──┘    (无需 LLM)

Synthesize: 基于 #E1=..., #E2=..., #E3=... 生成答案
```

ReWOO 只需 3 次 LLM 调用（Plan + Execute批处理 + Synthesize），而 ReAct 可能需要 N×M 次。

核心代码见 [rewoo.py](rewoo.py) 的 `plan()`, `execute_batch()`, `synthesize()`。

### 4. Self-Ask 模式

Self-Ask 通过**递归追问**来处理复杂推理：

```
问: Transformer 的作者是谁？他们为什么要提出这个架构？
  → 追问1: Transformer 的作者是谁？
  → 得到答案: Vaswani 等人
  → 追问2: 他们为什么提出这个架构？
  → 得到答案: 解决 RNN 无法并行化的问题
  → 综合答案
```

核心代码见 [self_ask.py](self_ask.py) 的 `should_ask_follow_up()` 和 `_answer_follow_up()`。

### 5. 四种模式对比

| 维度 | ReAct (Day09) | Plan-Execute | ReWOO | Self-Ask |
|------|:---:|:---:|:---:|:---:|
| LLM 调用次数 | 多（每步一次） | 中等（3-N次） | 少（3次） | 较多（N次追问） |
| 工具调用方式 | 串行 | 逐步串行 | 批量并行 | 按需串行 |
| 适用场景 | 简单灵活任务 | 多步骤结构化 | 无依赖并行查询 | 层层递进推理 |
| 可解释性 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| 执行效率 | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐ |

---

## 💡 实例演示

### 实例1：Plan-Execute 多步骤调研

```python
from plan_execute import PlanExecuteAgent
agent = PlanExecuteAgent()
result = agent.run("帮我调研 Python 在 AI 开发中的地位，并计算 2026-1991")
# Agent 自动规划: [搜索Python AI应用, 搜索AI开发趋势, 计算年份差]
# 逐步执行每个子任务，最后综合所有结果
```

### 实例2：ReWOO 并行工具调用

```python
from rewoo import ReWOOAgent
agent = ReWOOAgent()
result = agent.run("搜索深度学习信息，搜索神经网络信息，计算 100+200*3")
# 三个工具调用并行执行，大幅减少等待时间
```

### 实例3：Self-Ask 追问链推理

```python
from self_ask import SelfAskAgent
agent = SelfAskAgent()
result = agent.run("Transformer 架构的提出者是谁？主要解决了什么问题？")
# Agent 先查作者，根据结果决定追问"解决了什么问题"
```

**运行方法：**
```bash
cd phase3_agent/day12_advanced_agent_patterns
python example.py
```

---

## ✍️ 练习题

### 练习1：基础题
1. 运行 `python example.py`，观察三种模式的输出差异
2. 修改 `demo_plan_execute()` 中的任务字符串，测试不同的调研任务
3. 在 ReWOO 模式中添加第三个工具（如 `get_weather`），观察并行执行

### 练习2：进阶题
1. 给 Plan-Execute Agent 添加步骤验证：每步执行完后检查结果，不合格则重试
2. 为 ReWOO Agent 实现错误处理：如果某个工具调用失败，跳过继续执行其它调用
3. 改造 Self-Ask Agent，限制最大追问次数（防止无限循环）

### 练习3：挑战题
1. 实现一个"自适应 Agent 路由器"：根据任务类型自动在 ReAct / Plan-Execute / ReWOO / Self-Ask 之间选择
2. 实现 Plan-Execute 的"动态重规划"功能：执行中发现计划不合理时，重新规划剩余步骤

---

## 🔮 后一天知识展望

明天我们进入**多 Agent 协作系统**（Day13）。当一个 Agent 不够用时，我们让多个 Agent 分工协作——就像软件开发团队一样，不同的专家 Agent 各司其职，通过顺序、并行、投票等方式协同完成任务。

---

## 📝 今日总结

- ✅ Plan-Execute：先用 LLM 制定 JSON 格式计划，再逐步执行，适合结构化多步骤任务
- ✅ ReWOO：占位符 + 批量执行，LLM 调用从 N 次降到 3 次，效率最高
- ✅ Self-Ask：递归追问链，每步结果决定下一步方向，适合需要深度推理的问题
- ✅ 所有模式使用原生 openai SDK，零 LangChain 依赖
- ✅ 没有"银弹"模式——根据任务特点选择最合适的

---

## 🚀 下一步

1. 完成所有练习题
2. 思考：你工作中的哪些任务适合哪种 Agent 模式？
3. 尝试把 Day11 的 MemoryAgent 改造成 Plan-Execute 模式

---

## 📖 参考资料

- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- [Plan-and-Solve Prompting](https://arxiv.org/abs/2305.04091)
- [ReWOO: Decoupling Reasoning from Observations](https://arxiv.org/abs/2305.18323)
- [Self-Ask: Measuring and Narrowing the Compositionality Gap](https://arxiv.org/abs/2210.03350)
- [OpenAI Function Calling 文档](https://platform.openai.com/docs/guides/function-calling)
