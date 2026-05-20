# Day 19: RAG 评估体系 — 检索质量 + 回答质量 + 多轮对话

> 🎯 **学习目标**
>
> - 掌握 RAG 回答质量的三大评估维度：忠实度、相关性、完整性
> - 掌握经典 IR 评估指标：Precision@K、Recall@K、MRR、NDCG@K
> - 理解每个指标的含义、计算公式和适用场景
> - 掌握多轮对话式 RAG：上下文继承、查询重写、对话历史管理
> - 从零实现评估指标（不依赖 RAGAS 等第三方库）

---

## 📖 前一天知识回顾

昨天（Day18）我们大幅提升了检索质量：
- ✅ 混合检索（BM25 + Vector + RRF 融合）
- ✅ CrossEncoder 重排序

**问题：** 怎么证明检索优化真的"有效"？怎么知道 RAG 生成的答案有没有"编造内容"（幻觉）？

**今天，我们建立评估体系——给 RAG 系统量体温、测血压！**

---

## 📚 新知识讲解

### 1. 为什么 RAG 评估很重要？

**比喻**：就像软件开发需要测试，RAG 系统也需要评估：
- 不加评估盲目优化 = 不知道自己在往哪个方向走
- 评估指标 = 导航仪，告诉你离目标有多远

### 2. RAG 回答质量的三维评估

见 [rag_evaluation.py](rag_evaluation.py) — `RAGEvaluator` 类：

#### 2.1 忠实度（Faithfulness）

**问题：回答是否严格基于检索到的文档？有没有编造？**

```
评估流程：
1. LLM 提取回答中的所有"声明"（claims）
2. 逐条检查每条声明是否被 context_docs 支持
3. 忠实度 = 有支撑的声明 / 总声明数
```

#### 2.2 文档相关性（Relevance）

**问题：检索到的文档和用户查询的相关程度？**

```
评估方法：
1. 将 query 和每篇 doc 分别向量化
2. 计算余弦相似度
3. 取均值作为整体相关性得分
```

#### 2.3 完整性（Completeness）

**问题：回答是否覆盖了文档中的关键技术点？**

```
评估流程：
1. LLM 从文档中提取关键信息点
2. 逐条检查每个关键信息点是否在回答中被覆盖
3. 完整性 = 覆盖的信息点 / 总关键信息点
```

### 3. 经典 IR 检索评估指标

见 [rag_evaluation.py](rag_evaluation.py) — `RetrievalEvaluator` 类：

| 指标 | 公式 | 含义 |
|------|------|------|
| **P@K** | `|Top-K ∩ Relevant| / K` | 前K个结果中相关的比例 |
| **R@K** | `|Top-K ∩ Relevant| / |Relevant|` | 前K个结果覆盖了多少相关文档 |
| **MRR** | `Σ(1/rank_q) / |Q|` | 首个相关结果排名的倒数均值 |
| **NDCG@K** | `DCG/IDCG` | 考虑排名位置的相关性评估 |

**P@K vs R@K 的直觉：**
- P@5 = 0.8 → 前 5 个结果中 80% 是相关的（精度好）
- R@5 = 1.0 → 前 5 个结果覆盖了全部相关文档（召回全）
- P@5 = 1.0, R@5 = 0.5 → 前 5 个都相关，但漏了一半相关文档

### 4. 对话式 RAG（ConversationRAG）

见 [conversation_rag.py](conversation_rag.py) — `ConversationRAG` 类：

```
用户: "Python 是谁创建的？"  → 检索"Python 创建者" → 回答
用户: "它的设计哲学是什么？" → 先查询重写："Python 的设计哲学" → 检索 → 回答
       ↑ 不重写的话，"它的"没法检索
```

核心功能：
- 对话历史维护（保留上下文）
- 指代消解的查询重写
- 多轮对话管理（会话隔离）

---

## 💡 实例演示

完整演示见 [example.py](example.py)，包含三个环节：

1. **检索质量评估** — 用模拟数据计算 P@K、R@K、NDCG@K、MRR
2. **RAG 回答质量评估** — 忠实度、相关性、完整性的完整评估流程
3. **对话式 RAG** — 5 轮对话演示上下文继承和查询重写

**运行方法：**
```bash
cd phase4_rag/day19_rag_evaluation
python example.py
```

---

## ✍️ 练习题

### 练习1：基础题
1. 运行 `python example.py`，理解每个评估指标的输出含义
2. 修改检索评估中的 `retrieved` 和 `relevant` 列表，观察指标如何变化
3. 在对话式 RAG 中添加自己的知识文档，测试上下文追问效果

### 练习2：进阶题
1. 给 `RAGEvaluator` 添加"答案简洁度"评估：回答是否包含过多无关内容
2. 实现 `F1@K` 指标：F1 = 2 × P@K × R@K / (P@K + R@K)
3. 给 `ConversationRAG` 添加"会话摘要"：超过 N 轮后自动压缩历史

### 练习3：挑战题
1. 构建一个"评估基准数据集"：10 个查询 + ground truth + 相关文档标注
2. 对比 Day17 的基础 RAG 和 Day18 的优化 RAG 在各指标上的差异（量化优化效果）

---

## 🔮 后一天知识展望

评估体系就绪，明天（Day20）是 Phase 4 最后一天——**生产级 RAG**。我们将整合所有基础设施（配置管理、结构化日志、TTL+LRU 缓存、指数退避重试、混合检索、重排序、指标收集）构建一个真正"能扛"的生产级 RAG 系统。

---

## 📝 今日总结

- ✅ RAG 评估 = 检索质量（离线的 IR 指标） + 回答质量（LLM 驱动判断）
- ✅ Faithfulness 检测幻觉，Relevance 评估检索，Completeness 衡量覆盖度
- ✅ P@K、R@K、MRR、NDCG@K 是信息检索的四大经典指标
- ✅ ConversationRAG 通过查询重写实现多轮连贯对话
- ✅ 所有评估指标从零实现，不依赖第三方评估库
- ✅ 无法度量就无法改进——评估是 RAG 优化的前提

---

## 🚀 下一步

1. 完成所有练习题
2. 用今天学的评估指标测试 Day17/Day18 的 RAG 系统
3. 思考：在实际生产环境中，哪个评估维度最重要？为什么？

---

## 📖 参考资料

- [RAGAS: Evaluation framework for RAG](https://docs.ragas.io/)（可选了解）
- [Precision and Recall (Wikipedia)](https://en.wikipedia.org/wiki/Precision_and_recall)
- [NDCG (Wikipedia)](https://en.wikipedia.org/wiki/Discounted_cumulative_gain)
- [MRR (Wikipedia)](https://en.wikipedia.org/wiki/Mean_reciprocal_rank)
- [Evaluating RAG Pipelines (Anthropic)](https://docs.anthropic.com/en/docs/build-with-claude/embeddings)
