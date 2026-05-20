# Day 07: Context Engineering — 上下文工程

> 🎯 **学习目标**
>
> - 理解Context Engineering vs 传统Prompt Engineering的本质区别
> - 掌握System Message的设计原则（角色、边界、输出格式）
> - 学会多维度上下文的构建：工具描述 + 记忆 + 外部知识
> - 理解Few-shot示例的动态选择和注入策略
> - 能设计生产级的LLM上下文结构

---

## 📖 前一天知识回顾

昨天我们学习了LLM的基础概念和openai SDK的使用：
- ✅ LLM通过预测下一个token逐字生成文本
- ✅ openai SDK统一调用各种兼容API
- ✅ temperature控制创造性，max_tokens控制输出长度
- ✅ 多轮对话需要每次发送完整的历史消息

---

## 📚 新知识讲解

### 1. 从Prompt Engineering到Context Engineering

**传统Prompt Engineering**：把LLM当作需要"咒语"的魔法盒，反复手工调优一段prompt。

**Context Engineering**：把LLM当作一个**可编程的计算单元**，系统性地设计它能看到的所有信息。

```
┌─────────────────────────────────────────────────┐
│                 Context = 上下文                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ System   │ │ Tools    │ │ Retrieved        │ │
│  │ Message  │ │ Description│ │ Documents (RAG)  │ │
│  │ (角色+规则)│ │ (工具说明) │ │ (检索到的知识)   │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Few-shot │ │ Memory   │ │ User             │ │
│  │ Examples │ │ (对话历史) │ │ Message          │ │
│  │ (示例)    │ │          │ │ (用户当前输入)    │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
└─────────────────────────────────────────────────┘
```

**核心理念转变**：
| 传统思维 | Context Engineering 思维 |
|---------|------------------------|
| "写一个更好的prompt" | "设计一个更好的上下文结构" |
| 手工调优一段文字 | 系统性地管理多维信息 |
| 关注user消息 | 关注system + tools + 历史 + 知识 |
| 经验直觉驱动 | 结构化设计 + A/B测试驱动 |

### 2. System Message 设计（最重要的上下文）

**比喻**：System Message就像给员工的**岗位说明书**——不是每句话都要重复，而是设定好角色、职责和边界。

**设计原则：**

```python
# 不好的System Message：太模糊
"你是一个有用的助手"

# 好的System Message：角色 + 规则 + 输出格式 + 边界
"""你是一个Python编程专家，职责是帮助用户解决代码问题。

## 规则
1. 始终给出可运行的完整代码
2. 代码需要中文注释解释关键逻辑
3. 如果问题有多个解法，列出并比较优劣

## 输出格式
- 先给出简短的口头解释（1-2句话）
- 再给出代码块
- 最后说明注意事项

## 边界
- 只回答编程相关问题
- 不猜测用户的环境配置
- 不确定时明确说明"""
```

### 3. 工具描述即上下文

在后续Agent开发中，工具描述（Tool Description）是决定LLM能否正确选择和调用工具的关键上下文。一个好的工具描述需要包含：**功能描述 + 参数说明 + 使用场景 + 返回格式**。

我们将在Day08（Function Calling）和Day10（MCP协议）中深入学习。

### 4. 上下文窗口管理

**比喻**：上下文窗口就像**工作台桌面**——空间有限，放太多东西会乱，需要取舍。

```python
# 上下文窗口管理策略
messages = [
    {"role": "system", "content": system_prompt},  # 始终保留（固定开销）
    # ... 历史对话 ...  # 可能需要截断/压缩
    {"role": "user", "content": current_query}  # 始终保留当前问题
]

# 策略1: 滑动窗口（只保留最近N轮对话）
def sliding_window(messages, max_turns=10):
    """保留system消息 + 最近N轮对话"""
    system_msgs = [m for m in messages if m["role"] == "system"]
    dialog = [m for m in messages if m["role"] != "system"]
    return system_msgs + dialog[-(max_turns * 2):]  # 每轮=user+assistant

# 策略2: 摘要压缩（用LLM压缩历史为摘要）
# 根据token预算动态调整
```

### 5. Few-shot示例的策略

在上下文中注入示例能让LLM的输出质量大幅提升：

```python
few_shot_context = """
输入: 帮我写一个快速排序 → 意图: 代码生成, 语言: Python
输入: 这段代码有什么bug → 意图: 代码审查
输入: 今天天气怎么样 → 意图: 信息查询
"""
# 选择与当前问题最相似的2-3个示例放入上下文
```

---

## 💡 实例演示

### 实例1：System Message 的 A/B 对比

完整代码见 [context_engineering.py](context_engineering.py) 的 `demo_system_design()`。

### 实例2：上下文预算管理

完整代码见 [context_engineering.py](context_engineering.py) 的 `demo_context_budget()`。

### 实例3：结构化输出控制

完整代码见 [context_engineering.py](context_engineering.py) 的 `demo_structured_output()`。

**运行方法：**
```bash
python context_engineering.py
```

---

## ✍️ 练习题

### 练习1：基础题

1. 写3个不同角色的System Message（客服/教师/程序员），用相同问题测试回复差异
2. 给一个编程助手的System Message加上输出格式要求（必须包含代码块）
3. 计算一段对话的总token数（估算即可），判断是否超出128K上下文窗口

### 练习2：进阶题

1. 实现滑动窗口上下文管理：保留最近5轮对话 + system消息
2. 设计一个Few-shot示例注入策略：从一组示例中选最相关的2个
3. 写一个System Message，让LLM在不确定时明确回答"我不确定"而不是编造

### 练习3：挑战题

实现一个完整的上下文管理器（ContextManager类）：
- 支持添加/移除system消息
- 自动截断过长的历史对话（滑动窗口）
- 支持注入和检索few-shot示例
- 提供token预算的估算和警告
- 支持上下文的序列化和恢复

---

## 🔮 后一天知识展望

明天我们将学习 **Function Calling（函数调用）**——让LLM不仅能聊天，还能调用外部工具执行实际操作。

---

## 📝 今日总结

今天我们学习了：
- ✅ Context Engineering vs Prompt Engineering 的本质区别
- ✅ System Message 的设计原则（角色/规则/格式/边界）
- ✅ 多维度上下文的组成（system + tools + memory + knowledge）
- ✅ 上下文窗口管理策略（滑动窗口、摘要压缩）
- ✅ Few-shot示例的动态选择

**关键要点：**
1. **Context = LLM能看到的全部信息**，不只是user消息
2. **System Message 是最重要的基础设施**，设计好一次，持续受益
3. **工具描述是上下文的关键部分**，直接影响LLM的选择正确性
4. **上下文有token成本**，需要管理窗口大小

---

## 🚀 下一步

1. 完成所有练习题
2. 尝试为你常用的场景设计一套System Message模板
3. 准备好学习明天的Function Calling

**从"写prompt"升级到"设计context"！** 💪

---

## 📖 参考资料

- [Anthropic — Context Engineering](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
- [OpenAI — Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [OpenAI — Token Estimation](https://platform.openai.com/tokenizer)