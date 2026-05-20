# Day 08: Function Calling — 让LLM使用工具

> 🎯 **学习目标**
>
> - 理解Function Calling的原理：LLM如何"选择"和"调用"工具
> - 掌握使用原生openai SDK实现Function Calling（tools参数）
> - 学会设计工具描述（JSON Schema）让LLM准确匹配工具
> - 理解完整的Tool Calling Loop
> - 实战：天气查询、计算器、数据库查询等多工具场景

---

## 📖 前一天知识回顾

昨天我们学习了Context Engineering：
- ✅ System Message的设计原则（角色/规则/格式/边界）
- ✅ 上下文窗口管理和token预算
- ✅ **工具描述本身就是上下文的关键部分**

今天，我们让LLM真正地**使用工具**！

---

## 📚 新知识讲解

### 1. 什么是Function Calling？

**比喻**：LLM就像一个**只会说话的经理**——它能分析问题、制定计划，但不会动手。Function Calling就是给经理配上一群**能做事的员工**（工具函数），经理判断需要谁干活，员工干完活把结果汇报给经理。

```
用户: "北京今天天气怎么样？"
  ↓
LLM思考: 我需要查天气 → 调用 get_weather("北京")
  ↓
get_weather函数 → {"temperature": 20, "condition": "晴"}  (实际执行)
  ↓
LLM: "北京今天晴，温度20°C"  (把结果转成自然语言)
```

### 2. 工具定义（JSON Schema）

新版API使用 `tools` 参数（替代旧版 `functions`）：

```python
tools = [
    {
        "type": "function",  # 固定值
        "function": {
            "name": "get_weather",  # 函数名
            "description": "获取指定城市的天气信息",  # 描述（决定LLM何时调用！）
            "parameters": {  # JSON Schema格式的参数定义
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'"
                    }
                },
                "required": ["city"]
            }
        }
    }
]
```

### 3. Tool Calling Loop（核心流程）

```
┌──────────────────────────────────────────────────────────┐
│                    Tool Calling Loop                       │
│                                                           │
│  1. 用户输入 + tools定义 → 发给LLM                         │
│  2. LLM返回:                                              │
│     - 要么: tool_calls (要调用哪些函数、什么参数)           │
│     - 要么: 直接文本回复 (不需要调用工具)                   │
│  3. 如果tool_calls:                                       │
│     a. 执行对应的Python函数                                │
│     b. 把结果追加到messages中 (role: "tool")               │
│     c. 回到步骤1，让LLM基于结果生成最终回复                 │
│  4. 完成，返回最终回复给用户                                │
└──────────────────────────────────────────────────────────┘
```

### 4. 多工具并行调用

LLM可以同时调用多个独立工具（如同时查北京和上海的天气），然后汇总结果。

---

## 💡 实例演示

### 实例1：基础Function Calling — 天气查询

完整代码见 [function_calling.py](function_calling.py) 的 `demo_basic_function_calling()`。

### 实例2：多工具场景 — 天气 + 计算器 + 时间

完整代码见 [function_calling.py](function_calling.py) 的 `demo_multi_tools()`。

### 实例3：Tool Calling Loop 完整实现

完整代码见 [function_calling.py](function_calling.py) 的 `tool_loop()`——这是明天Agent基础的核心！

**运行方法：**
```bash
python function_calling.py
```

---

## ✍️ 练习题

### 练习1：基础题

1. 定义一个"获取当前时间"的工具，让LLM能回答"现在几点了"
2. 用 tools 参数（而非旧的 functions 参数）实现天气查询
3. 写一个能同时查天气和计算数学表达式的多工具场景

### 练习2：进阶题

1. 实现完整的 Tool Calling Loop（循环直到LLM不再请求工具调用）
2. 给工具添加错误处理：函数执行失败时，把错误信息作为结果返回给LLM
3. 实现工具调用的日志记录（记录每次调用、参数、结果、耗时）

### 练习3：挑战题

实现一个可扩展的工具系统（ToolRegistry）：
- 支持动态注册/移除工具
- 自动从函数签名生成JSON Schema
- 支持工具调用的权限控制（某些工具需要用户确认）
- 支持工具调用的超时和重试

---

## 🔮 后一天知识展望

明天我们将学习 **Agent基础**——基于今天的Tool Calling Loop，从零实现ReAct（推理-行动-观察）循环，构建第一个真正的AI Agent！

---

## 📝 今日总结

今天我们学习了：
- ✅ Function Calling的核心原理：LLM选择工具→执行→反馈结果
- ✅ 使用原生SDK的 `tools` 参数定义工具
- ✅ JSON Schema格式的工具描述
- ✅ 完整的Tool Calling Loop（循环执行直到完成）
- ✅ 多工具并行调用

**关键要点：**
1. **LLM不执行工具**，它只输出"我想调哪个函数、什么参数"
2. **tool description 是最重要的上下文**，写得不好LLM就选错工具
3. **使用新版 `tools` 参数**（非旧版 `functions`）
4. **Tool Calling Loop = Agent的基础**，明天将在它的基础上构建完整Agent

---

## 🚀 下一步

1. 完成所有练习题
2. 理解Tool Calling Loop的每一步
3. 准备好明天从零构建Agent

**离Agent只剩一步！** 🚀

---

## 📖 参考资料

- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [JSON Schema规范](https://json-schema.org/)
- [OpenAI Tools API Reference](https://platform.openai.com/docs/api-reference/chat/create#chat-create-tools)