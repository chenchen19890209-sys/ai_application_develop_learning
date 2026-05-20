# Day 09: Agent基础 — 从零实现ReAct Agent

> 🎯 **学习目标**
>
> - 理解Agent的核心架构：感知→思考→行动→观察
> - 从零实现ReAct（Reasoning + Acting）循环（不依赖任何框架）
> - 掌握Agent的停止条件设计
> - 理解Agent vs 固定Workflow的本质区别
> - 实战：构建能自主查询天气、做计算、管理待办事项的Agent

---

## 📖 前一天知识回顾

昨天我们学习了Function Calling和Tool Calling Loop：
- ✅ LLM通过 `tools` 参数知道有哪些工具可用
- ✅ Tool Calling Loop: 用户输入 → LLM选择工具 → 执行 → 反馈 → 循环
- ✅ LLM可能并行调用多个独立工具

**今天，我们在Tool Calling Loop的基础上构建完整的Agent！**

---

## 📚 新知识讲解

### 1. 什么是Agent？

**比喻**：如果LLM是"大脑"，常规程序是"肌肉记忆"，那Agent就是**一个有自主决策能力的人**——它能理解任务、制定计划、使用工具、检查结果、调整策略。

```
┌─────────────────────────────────────────────────┐
│                  Agent 架构                       │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐ │
│  │ 思考(Reason)│→│ 行动(Act) │→│ 观察(Observe) │ │
│  │  分析局势  │  │ 调用工具  │  │  获取结果     │ │
│  └──────────┘  └──────────┘  └───────────────┘ │
│        ↑                              ↓          │
│        └──────── 循环 ←───────────────┘          │
│                                                  │
│  组件: LLM + Tools + Memory + Planning          │
└─────────────────────────────────────────────────┘
```

**Agent vs 固定Workflow（管道）**：

| 维度 | 固定Workflow | Agent |
|------|-------------|-------|
| 流程 | 预定义的A→B→C | 动态决策，路径不固定 |
| 适应性 | 遇到意外就出错 | 能应对意外情况 |
| 实现 | 简单的函数管道 | 需要工具调用循环 |
| 适用 | 输入输出明确的固定任务 | 需要自主判断的开放任务 |

### 2. ReAct 模式（Reasoning + Acting）

**比喻**：ReAct就像一个有经验的维修工——先分析问题（Reason）、再动手操作（Act）、观察结果（Observe）、决定下一步。

```
用户: "帮我查杭州气温，如果高于25°C建议穿短袖，否则穿长袖"

ReAct循环:
  Step 1: Thought: 需要查杭州天气 → Action: get_weather("杭州")
  Step 2: Observation: 温度22°C → Thought: 低于25°C → 不需要更多信息
  Final: "杭州温度22°C，建议穿长袖"
```

### 3. 停止条件设计

Agent需要知道什么时候该"停"：

```python
# 停止条件1: LLM返回了纯文本回复（不调用工具）
if not message.tool_calls:
    return message.content

# 停止条件2: 达到最大循环次数（安全阀）
if iteration >= max_iterations:
    return "任务超时，已超过最大步骤数"

# 停止条件3: 用户确认模式（高风险操作需要用户approve）
if tool.requires_confirmation:
    user_approved = ask_user_for_confirmation(tool_call)
```

### 4. Agent的记忆系统

Agent需要两种记忆：
- **短期记忆（Working Memory）**：当前会话的对话历史（messages列表）
- **长期记忆（Persistent Memory）**：跨会话的用户偏好、历史行为

---

## 💡 实例演示

### 实例1：从零实现ReAct Agent

完整代码见 [agent_basics.py](agent_basics.py) 的 `ReActAgent` 类——不使用任何框架，纯原生SDK实现。

### 实例2：Agent的思考过程可视化

完整代码见 [agent_basics.py](agent_basics.py) 的 `run_with_trace()` 方法。

**运行方法：**
```bash
python agent_basics.py
```

---

## ✍️ 练习题

### 练习1：基础题

1. 基于Tool Calling Loop实现一个简单的ReAct Agent类
2. 给Agent新增一个"生成随机数"的工具，观察Agent如何选择工具
3. 为Agent添加步骤数限制（超过5步自动停止）

### 练习2：进阶题

1. 实现Agent的思考过程可视化（每一步打印 Thought → Action → Observation）
2. 添加Agent的记忆系统：在session内记住用户的偏好和之前的行为
3. 实现一个"用户确认模式"：当Agent要执行高风险操作时，先请求用户确认

### 练习3：挑战题

实现一个完整的Agent框架，支持：
- 可插拔的工具系统（注册/移除/发现工具）
- 可配置的停止条件（多种条件组合）
- 会话级别的记忆管理（短期/长期）
- Agent执行追踪和回放（记录每一步的输入输出）
- 错误恢复（工具调用失败时的fallback策略）

---

## 🔮 后一天知识展望

明天我们将学习 **MCP协议（Model Context Protocol）**—— 一种标准化的工具暴露方式，让任何Agent都能接入任何工具，实现真正的工具生态互通。

---

## 📝 今日总结

今天我们学习了：
- ✅ Agent的核心架构：感知→思考→行动→观察循环
- ✅ 从零实现ReAct Agent（零框架依赖）
- ✅ Agent的停止条件设计
- ✅ Agent的记忆系统

**关键要点：**
1. **Agent = LLM + Tools + Memory + Loop**，关键在自主决策能力
2. **ReAct = 思考→行动→观察的循环**，直到任务完成
3. **Agent替代不了固定Workflow**，简单任务不需要Agent
4. **停止条件非常重要**，没有它Agent会无限循环

---

## 🚀 下一步

1. 完成所有练习题
2. 理解ReAct循环的每个环节
3. 准备好学习MCP协议

**恭喜！你已经构建了第一个真正的AI Agent！** 🎉

---

## 📖 参考资料

- [ReAct论文](https://arxiv.org/abs/2210.03629)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Anthropic Tool Use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)