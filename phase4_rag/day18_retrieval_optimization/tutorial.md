# Day 18: 检索优化 — 混合检索 + RRF 融合 + 重排序

> 🎯 **学习目标**
>
> - 理解 BM25（稀疏检索）和向量检索（稠密检索）各自的优劣势
> - 掌握 RRF（Reciprocal Rank Fusion）融合算法：兼顾关键词和语义
> - 掌握 CrossEncoder 重排序：精排阶段的深度语义匹配
> - 了解 LLM Reranker：用大语言模型评估文档相关性
> - 理解"粗排-精排"两阶段检索架构

---

## 📖 前一天知识回顾

昨天（Day17）我们构建了完整的文档处理和 RAG 系统：
- ✅ 三种分块策略和 RAGBuilder 一站式索引
- ✅ 用 ChromaDB 存储向量并检索

**问题：** Day17 只用向量检索。如果用户查询包含精确关键词（如"BM25 算法"），向量检索可能返回语义相关但不含关键词的文档。反过来，如果用户问"电脑怎么修"，BM25 可能匹配不到"计算机维修"。

**今天，我们把两种方法融合起来，取长补短！**

---

## 📚 新知识讲解

### 1. BM25 vs 向量检索：互补的两种力量

| 维度 | BM25 稀疏检索 | 向量语义检索 |
|------|:---:|:---:|
| 匹配原理 | 关键词词频（TF-IDF 变体） | 语义向量相似度 |
| "苹果手机" vs "iPhone" | ❌ 不匹配（不同词） | ✅ 语义匹配 |
| "Python" vs "Python" | ✅ 精确匹配 | ✅ 也能匹配 |
| 是否需要 GPU | ❌ 不需要 | 🟡 推荐 |
| 速度 | 非常快 | 较快 |

**比喻**：BM25 像"查目录"——必须精确匹配关键词；向量像"问图书管理员"——理解你的意图。

见 [hybrid_retrieval.py](hybrid_retrieval.py) 的 `BM25Retriever` 和 `VectorRetriever` 类。

### 2. RRF（Reciprocal Rank Fusion）融合算法

```
文档 d 的 RRF 分数 = Σ 1/(k + rank_i(d))

其中:
- k = 60（平滑常数，标准值）
- rank_i(d) = 文档 d 在检索方法 i 中的排名

直觉：
- 在两处都排名靠前的文档 → RRF 分数高 → 最终排名高
- 只在一处排名靠前的文档 → RRF 分数低 → 排名降低
```

```
查询: "Python 编程语言"
    BM25 排名          向量排名          RRF 融合
1. Python教程        1. 编程入门        1. Python教程 (BM25#1, Vec#2)
2. 编程入门          2. Python教程      2. 编程入门 (BM25#2, Vec#1)
3. Java编程          3. 软件工程        3. Java编程 (BM25#3, Vec#5)
```

### 3. 两阶段检索架构：粗排 → 精排

```
粗排（召回阶段）              精排（重排序阶段）
速度快、精度有限              速度慢、精度高
┌──────────────┐            ┌──────────────────┐
│ BM25 (Top-20) │──┐         │ CrossEncoder     │
├──────────────┤  ├─RRF──▶│ (Top-5→Top-3)    │──▶ 最终结果
│ Vector(Top-20)│──┘         │ 或 LLM Reranker  │
└──────────────┘            └──────────────────┘
```

### 4. CrossEncoder 重排序

见 [reranker.py](reranker.py) — `CrossEncoderReranker` 类：

**Bi-Encoder vs Cross-Encoder：**
- Bi-Encoder：query 和 doc 独立编码，用向量相似度匹配（快但交互弱）
- Cross-Encoder：`[CLS] query [SEP] doc` 一起输入 Transformer（慢但精度高）

```python
reranker = CrossEncoderReranker()  # BAAI/bge-reranker-base
# 将混合检索的 Top-20 候选精排为 Top-3
results = reranker.rerank(query, candidates, top_k=3)
```

### 5. LLM Reranker（可选最终精排）

用大语言模型深度理解查询和文档的语义关系，对少量候选（3-5篇）进行最终打分排序。

优点：理解力最强；缺点：速度慢、有 API 成本。

---

## 💡 实例演示

完整演示见 [example.py](example.py)，包含四个环节：

1. **文档语料展示** — 18 篇中文文档
2. **三种检索对比** — BM25 Only vs Vector Only vs Hybrid(RRF)
3. **重排序 Pipeline** — 混合检索 → CrossEncoder 精排 → LLM 精排
4. **方法对比表**

**运行方法：**
```bash
cd phase4_rag/day18_retrieval_optimization
python example.py
```

---

## ✍️ 练习题

### 练习1：基础题
1. 运行 `python example.py`，观察同一查询下三种检索方法的结果差异
2. 修改 RRF 的 k 值（60 → 30 和 60 → 120），观察融合结果的变化
3. 在 `DEMO_DOCUMENTS` 中添加 3 篇你自己的文档并重新对比

### 练习2：进阶题
1. 实现"加权 RRF"：给 BM25 和向量检索不同的权重（如 BM25 ×0.3 + Vector ×0.7）
2. 给 `HybridRetriever` 添加 `add_document()` 增量索引方法
3. 对比 CrossEncoder 和 LLM Reranker 在相同候选集上的精排结果

### 练习3：挑战题
1. 实现"查询扩展"：检索前先用 LLM 把简短查询扩展为更详细的查询，再检索
2. 实现"多轮检索"：第一轮检索 → LLM 生成初步答案 → 用答案再检索 → 融合两轮结果

---

## 🔮 后一天知识展望

检索优化到极致之后，我们需要一把"尺子"来衡量效果。明天（Day19）我们将学习 **RAG 评估**——忠实度（Faithfulness）、相关性（Relevance）、完整性（Completeness）三大维度，以及经典的 IR 指标：Precision@K、Recall@K、MRR、NDCG。**无法度量就无法改进！**

---

## 📝 今日总结

- ✅ BM25 擅长精确关键词匹配，向量检索擅长语义理解——两者互补
- ✅ RRF（Reciprocal Rank Fusion）是一种无需训练的排名融合算法（k=60）
- ✅ 粗排（BM25+Vector→RRF）+ 精排（CrossEncoder/LLM）是工业标准架构
- ✅ CrossEncoder 重排序性价比较高，适合大多数场景
- ✅ LLM Reranker 适合对精度要求极高的最终精排环节

---

## 🚀 下一步

1. 完成所有练习题
2. 理解 RRF 公式中 k 参数对融合结果的敏感性
3. 思考：在你的项目场景中，粗排该取 Top-N 多少？精排该取 Top-K 多少？

---

## 📖 参考资料

- [Reciprocal Rank Fusion (RRF) explained](https://medium.com/@devalshah1619/mathematical-intuition-behind-reciprocal-rank-fusion-rrf-explained-in-2-minutes)
- [BGE Reranker 模型](https://huggingface.co/BAAI/bge-reranker-base)
- [BM25 算法详解](https://en.wikipedia.org/wiki/Okapi_BM25)
- [Hybrid Search with ChromaDB](https://docs.trychroma.com/guides/hyde)
