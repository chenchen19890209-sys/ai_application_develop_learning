# Day 11: 自定义工具与记忆系统 — Agent 的双手与大脑

> 🎯 **学习目标**
>
> - 掌握 MCP-native 工具类的设计与实现（WeatherTool、CalculatorTool、TodoTool、SearchTool、FileTool）
> - 理解 Agent 的三级记忆架构：工作记忆(任务级) → 短期记忆(会话级) → 长期记忆(持久化)
> - 学会将工具调用和记忆检索融合到 ReAct Tool Calling Loop 中
> - 掌握长期记忆的 LLM 自动提取技术（JSON 结构化输出）
> - 实战：构建 MemoryAgent — 拥有记忆的智能 Agent

---

## 📖 前一天知识回顾

Phase 2 我们完成了 LLM 核心能力的全链路学习：
- ✅ Day06: LLM 基础调用（openai SDK）
- ✅ Day07: Context Engineering（系统消息、记忆管理、多维上下文）
- ✅ Day08: Function Calling（原生 tools 参数、JSON Schema）
- ✅ Day09: ReAct Agent（手写 tool-calling loop）
- ✅ Day10: MCP 协议（工具标准化、跨框架复用）

**进入 Phase 3，我们将 Agent 推向生产深度。今天首先解决两个核心问题：自定义工具（Agent 的"双手"）和记忆系统（Agent 的"大脑"）。**

---

## 📚 新知识讲解

### 1. Agent 的三级记忆架构

**比喻**：像一个高效的程序员工作状态：
- **工作记忆** = 便签纸（当前任务的关键信息，任务完成就丢弃）
- **短期记忆** = 今天的聊天记录（本次会话的完整上下文）
- **长期记忆** = 笔记软件（跨会话持久化的知识）

```
┌─────────────────────────────────────────────────────────┐
│               Agent 三级记忆架构                          │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  工作记忆     │  │  短期记忆     │  │  长期记忆     │  │
│  │ WorkingMemory │  │ ShortTerm    │  │ LongTerm     │  │
│  │              │  │ Memory       │  │ Memory       │  │
│  │ 作用域: 单任务 │  │ 作用域: 单会话 │  │ 作用域: 跨会话 │  │
│  │ 容量: 有限    │  │ 容量: 滑动窗口 │  │ 容量: 持久存储 │  │
│  │ 特点: LRU淘汰 │  │ 特点: FIFO淘汰│  │ 特点: JSON文件 │  │
│  │ 示例: 当前步骤 │  │ 示例: 对话历史 │  │ 示例: 用户偏好 │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  Agent 决策 = 工作记忆(当前) + 短期记忆(会话) + 长期记忆(全局)│
└─────────────────────────────────────────────────────────┘
```

### 2. MCP-native 工具设计

每个工具遵循 MCP 标准结构：
```python
class WeatherTool:
    name = "get_weather"           # 工具唯一标识
    description = "获取城市天气"     # LLM 选择工具的依据
    inputSchema = {                 # JSON Schema 参数定义
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称"}
        },
        "required": ["city"]
    }

    def execute(self, city: str) -> dict:
        # 返回 MCP 标准格式
        return {"content": [{"type": "text", "text": f"{city}天气..."}]}
```

**关键设计原则**：
- `description` 是 LLM 选择工具的唯二依据（另一个是 `inputSchema` 中的参数描述）
- 返回值遵循 MCP 标准格式 `{"content": [{"type": "text", "text": "..."}]}`
- `tools_to_openai_format()` 将工具列表转换为 OpenAI `tools` 参数

### 3. WorkingMemory — 任务级工作区

```python
class WorkingMemory:
    """OrderedDict 实现，LRU 淘汰"""
    def set(self, key, value):    # 写入工作记忆
    def get(self, key, default):  # 读取工作记忆
    def to_context(self):         # 格式化为 LLM 上下文
    def log_step(self, action, result):  # 记录执行步骤
```

### 4. ShortTermMemory — 会话级滑动窗口

```python
class ShortTermMemory:
    """滑动窗口管理对话历史，超限自动裁剪"""
    def add_user_message(self, content):
    def add_assistant_message(self, content):
    def get_messages(self) -> List[Dict]:  # OpenAI 兼容格式
    def _trim(self):                        # 保持 max_turns 条记录
```

### 5. LongTermMemory — 跨会话持久化

```python
class LongTermMemory:
    """JSON 文件存储 + LLM 自动提取"""
    def remember(self, key, value):         # 直接写入
    def recall(self, key, default=None):    # 精确读取
    def summarize_and_store(self, conversation):  # LLM 自动提取关键信息
    def get_all_memories(self) -> Dict:     # 全量读取
```

`summarize_and_store()` 使用 LLM 的 `response_format={"type": "json_object"}` 从对话中提取：
- `user_name`: 用户姓名
- `user_city`: 所在城市
- `user_role`: 职业角色
- `user_interest`: 关注话题
- `user_preference`: 回答偏好

---

## 💡 实例演示

完整代码文件结构：
```
day11_custom_tools_memory/
├── tools.py              # 5 个 MCP-native 工具类
├── memory.py             # 三级记忆系统
├── agent_with_memory.py  # MemoryAgent — 记忆+工具融合
├── example.py            # 4 个演示
└── requirements.txt
```

### 实例1：工具展示

运行 [example.py](example.py) 的 `demo_tools_showcase()` —— 逐个测试 5 个工具，演示工具的 execute() 和标准返回格式。

### 实例2：短期记忆多轮对话

运行 `demo_short_term_memory()` —— 模拟多轮对话，展示滑动窗口如何自动管理上下文。

### 实例3：长期记忆跨会话

运行 `demo_long_term_memory()` —— 演示 LLM 自动从对话中提取关键信息并持久化。

### 实例4：MemoryAgent 完整流程

运行 `demo_memory_agent()` —— MemoryAgent 融合长期记忆（用户偏好）+ 短期记忆（对话上下文）+ 工作记忆（任务状态）进行工具调用。

**运行方法：**
```bash
cd phase3_agent/day11_custom_tools_memory
pip install -r requirements.txt
python example.py
```

---

## ✍️ 练习题

### 练习1：基础题

1. 给 `tools.py` 新增一个 `TranslateTool`（翻译工具），遵循 MCP 格式
2. 测试 `ShortTermMemory` 的滑动窗口行为（发送 10 条消息，观察 max_turns=5 时的裁剪）
3. 修改 `LongTermMemory` 的存储路径，观察 JSON 文件的变化

### 练习2：进阶题

1. 将 Day10 的 MCP Server 中的工具注册到 MemoryAgent 中
2. 给 `summarize_and_store()` 的 prompt 增加字段：用户技术栈、用户项目名称
3. 实现 `ShortTermMemory` 的"重要消息标记"功能（被标记的消息不会被裁剪）

### 练习3：挑战题

实现一个基于向量数据库的 LongTermMemory：
- 将每段记忆编码为向量存入 ChromaDB
- 查询时用语义搜索而非精确 key 匹配
- 支持"模糊回忆"——不记得精确 key 也能找到相关信息

---

## 🔮 后一天知识展望

明天我们学习 Plan-Execute、ReWOO、Self-Ask 三种高级 Agent 模式，它们在 ReAct 循环之上提供了更高效的推理和工具调用策略。

---

## 📝 今日总结

今天我们学习了：
- ✅ 5 个 MCP-native 工具类的设计与实现
- ✅ 三级记忆架构：WorkingMemory / ShortTermMemory / LongTermMemory
- ✅ LLM 自动提取长期记忆（JSON 结构化输出）
- ✅ MemoryAgent — 记忆 + 工具 + ReAct 融合

**关键要点：**
1. **工具 = Agent 的双手**，MCP 标准格式保证跨框架可复用
2. **三级记忆 = Agent 的大脑**，从任务级到会话级到持久化，逐层递进
3. **长期记忆用 LLM 自动提取**，而非手动标注
4. **所有组件都是独立的、可测试的单元**，零框架耦合

---

## 🚀 下一步

1. 完成所有练习题
2. 理解三级记忆各自的职责和生命周期
3. 尝试将 MemoryAgent 应用到实际场景（如客服对话、个人助理）

---

## 📖 参考资料

- [OpenAI Function Calling 文档](https://platform.openai.com/docs/guides/function-calling)
- [MCP 协议规范](https://spec.modelcontextprotocol.io/)
- [记忆系统设计模式](https://www.anthropic.com/research/agent-memory)
