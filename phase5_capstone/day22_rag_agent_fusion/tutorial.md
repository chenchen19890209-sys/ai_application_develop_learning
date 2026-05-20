# Day 22: RAG + Agent 融合系统

> 🎯 **学习目标**
>
> - 理解 Agent 与 RAG 融合的架构设计：Agent 作为核心调度器，RAG 作为知识检索工具
> - 掌握 QueryRouter：LLM 驱动的查询意图分类
> - 实现 RAGAgentCache：TTL + LRU 双层缓存策略
> - 构建 ConversationalRAGAgent：ReAct 循环 + 原生 Function Calling
> - 零 LangChain 依赖，100% 原生 openai SDK + Python

---

## 📖 Day 21 回顾

Day 21 我们完成了项目规划与架构设计：
- ✅ 需求分析 — LLM 驱动的结构化需求分解
- ✅ 技术选型 — 多维度评估矩阵
- ✅ 架构设计 — 模块化 + 依赖关系 + 接口定义
- ✅ 风险评估 — 概率×影响矩阵

**今天，进入课程精华！** 将 Phase 3 的 Agent（Day 9-15）和 Phase 4 的 RAG（Day 16-20）融合为一个完整的 AI 应用系统。

---

## 📚 新知识讲解

### 1. 融合架构：Agent 调度 RAG（而非固定管道）

**比喻**：传统 RAG 像一个固定菜单的餐厅——顾客来了先检索再上菜。Agent 调度的 RAG 像一个智能服务员——先理解需求，再决定是否需要去后厨（知识库）取菜。

```
❌ 固定管道模式：用户输入 → 检索 → 生成 → 输出
✅ Agent 调度模式：用户输入 → 路由分类 → Agent 决策 → [检索/计算/直接回答] → 输出
```

**为什么 Agent 调度更好？**
- 不是所有问题都需要检索（闲聊、简单常识）
- Agent 可以多次检索（复杂问题需要多轮搜索）
- Agent 可以根据检索结果决定下一步（检索质量不好时换关键词）

见 [agent.py](agent.py) 的架构注释图。

### 2. 查询路由：QueryRouter

**问题**：用户说"你好"时，不需要检索知识库；问"什么是 RAG"时，需要。

**解决方案**：QueryRouter 用 LLM 做轻量级意图分类：

```python
router = QueryRouter()
result = router.classify("什么是 RAG？")
# → {"route": "rag", "reason": "询问技术概念...", "confidence": 0.95}

result = router.classify("你好！")
# → {"route": "direct", "reason": "社交问候...", "confidence": 0.98}
```

三条路由路径：
| 路由 | 含义 | 示例 | Agent 行为 |
|------|------|------|-----------|
| `rag` | 需要知识库检索 | "什么是 RAG？" | 加载 search_knowledge 工具 |
| `direct` | 可直接回答 | "你好！" | 不加载工具，直接对话 |
| `tool` | 需要外部工具 | "算 123*456" | 加载 calculate 等工具 |

详见 [router.py](router.py)。

### 3. 检索缓存：RAGAgentCache

**问题**：用户在多轮对话中反复提到同一主题（如多次问 RAG 相关问题），每次都检索向量数据库很浪费。

**解决方案**：TTL（过期时间）+ LRU（淘汰策略）双层缓存。

```
缓存键 = MD5(查询文本)

操作流程：
get("什么是 RAG") → 检查缓存
  ├─ 命中 + 未过期 → 直接返回
  ├─ 命中 + 已过期 → 删除，重新检索
  └─ 未命中 → 检索 + 存入缓存
```

详见 [cache.py](cache.py)。

### 4. RAG 检索器：RAGRetriever

为 Agent 量身定制的检索器，封装了 Day 18 的混合检索能力：

- **向量检索**（语义匹配）：通过 sentence-transformers + ChromaDB
- **BM25 检索**（关键词匹配）：通过 rank_bm25 + jieba 分词
- **RRF 融合**：将两种检索结果合并排序

关键方法：
```python
retriever = RAGRetriever()
retriever.index(documents)       # 构建索引
results = retriever.search("什么是 RAG", top_k=3)  # 混合检索
formatted = retriever.format_for_llm(results)      # 格式化为 LLM 上下文
```

详见 [retriever.py](retriever.py)。

### 5. 核心融合：ConversationalRAGAgent

这是 Day 22 的核心——将以上所有组件融合为一个完整的 Agent 系统。

**ReAct 循环流程：**

```
1. 接收用户输入
2. QueryRouter 分类 → 决定工具集
3. 构建消息（系统提示 + 对话历史 + 用户输入）
4. LLM 推理（REAL openai SDK 调用）
   ├─ 决定调用工具 → 执行工具 → 观察结果 → 回到步骤 4
   └─ 无需调用 → 生成最终回复
5. 返回 AgentResponse（含答案 + 步骤 + 来源）
```

**RAG 检索作为工具的定义：**

```python
{
    "type": "function",
    "function": {
        "name": "search_knowledge",
        "description": "搜索内部知识库，获取技术概念、原理...",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索查询文本"},
                "top_k": {"type": "integer", "default": 3}
            },
            "required": ["query"]
        }
    }
}
```

**关键设计决策：**
- RAG 检索是 Agent 的一个**工具**，而非固定的前置步骤
- Agent **自己决定**是否需要检索、检索什么关键词、检索多少次
- 这比"先检索再回答"的固定管道更灵活，能处理更复杂的场景

详见 [agent.py](agent.py)。

### 6. 数据模型

见 [models.py](models.py) — 5 个核心数据结构：

```python
RAGResult       # RAG 检索结果（content, source, score, metadata）
ChatMessage     # 对话消息（role, content, tool_name, tool_call_id）
AgentAction     # Agent 单步动作（step, thought, tool_name, tool_input, tool_output）
AgentResponse   # Agent 最终回复（answer, actions, sources, total_steps, total_time_ms）
```

---

## 💡 实例演示

### 实例 1：路由分类

```python
from router import QueryRouter
router = QueryRouter()
result = router.classify("什么是 RAG 检索增强生成？")
print(result["route"])  # → "rag"
```

### 实例 2：缓存使用

```python
from cache import RAGAgentCache
cache = RAGAgentCache(max_size=100, ttl_seconds=300)
cache.set("什么是 RAG", results)    # 存入缓存
cached = cache.get("什么是 RAG")    # 命中缓存
print(cache.stats)                   # 查看缓存统计
```

### 实例 3：完整 Agent 对话

```python
from agent import ConversationalRAGAgent

agent = ConversationalRAGAgent()

# 知识检索型问题
response = agent.run("什么是 RAG？它为什么能减少幻觉？")
print(response.answer)     # 答案（含来源引用）
print(response.total_steps) # 执行步数
print(response.total_time_ms) # 耗时（毫秒）

# 多轮对话 — Agent 维护上下文
response = agent.run("它和传统搜索有什么区别？")
print(agent.stats)          # Agent 统计信息
```

**运行方法：**
```bash
cd phase5_capstone/day22_rag_agent_fusion
python example.py
```

---

## ✍️ 练习题

### 练习 1：基础题
1. 运行 `python example.py`，观察 6 个演示的输出
2. 修改 `DEMO_DOCUMENTS` 中的文档内容，添加你自己的领域知识
3. 查看路由分类结果，理解三种路由路径的差异

### 练习 2：进阶题
1. 给 `ConversationalRAGAgent` 添加 `search_knowledge` 的调用次数限制（防止无限检索）
2. 实现 `_get_weather_tool()`：添加天气查询工具，让 Agent 能查询天气
3. 给 `AgentResponse` 的 `sources` 字段填充实际的检索来源（当前为空）

### 练习 3：挑战题
1. 实现"多步检索"：Agent 先检索一次，根据结果决定是否需要换个关键词再检索
2. 添加"检索质量评估"：Agent 判断检索结果是否相关，不相关则自动重新检索
3. 构建一个"对比型"查询处理：用户问"A 和 B 的区别"，Agent 自动分别检索 A 和 B，再比较

---

## 🔮 后一天知识展望

有了 RAG + Agent 融合系统，明天（Day 23）我们进入最后一步：**Web UI 与部署**。我们将用 Streamlit 构建一个完整的对话界面，展示检索来源，并学习如何部署到生产环境。这是整个课程的收官之作！

---

## 📝 今日总结

- ✅ 融合架构：Agent 调度 RAG（非固定管道）— 更灵活、更智能
- ✅ QueryRouter：LLM 驱动的三路分类（rag / direct / tool）
- ✅ RAGAgentCache：TTL + LRU 双层缓存，避免重复检索
- ✅ RAGRetriever：封装 BM25 + 向量 + RRF 混合检索
- ✅ ConversationalRAGAgent：ReAct 循环 + 原生 Function Calling
- ✅ 多轮对话：Agent 维护上下文，支持指代消解
- ✅ 零 LangChain，100% 原生 openai SDK + Python

---

## 🚀 下一步

1. 完成所有练习题
2. 尝试用自己的知识库替换 DEMO_DOCUMENTS
3. 思考：什么场景下 Agent 调度模式比固定管道模式更有优势？

---

## 📖 参考资料

- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- [RAG: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)
- [Anthropic Context Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/context-engineering)
- [ChromaDB Documentation](https://docs.trychroma.com/)
