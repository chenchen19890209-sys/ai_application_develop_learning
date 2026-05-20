# Day 16: RAG 原理与向量数据库

> 🎯 **学习目标**
>
> - 理解 RAG（检索增强生成）的三段式架构：Indexing → Retrieval → Generation
> - 掌握 Embedding 的核心原理：文本 → 高维向量，语义距近=向量距近
> - 掌握 ChromaDB 的原生操作：创建 Collection、添加文档、语义查询
> - 理解余弦相似度的计算和意义
> - 构建第一个 RAG 系统：索引文档 → 检索 → LLM 生成答案

---

## 📖 Phase 3 回顾

Phase 3（Day11-15）我们深入了 Agent 的核心能力：
- ✅ 自定义工具与三级记忆系统
- ✅ Plan-Execute / ReWOO / Self-Ask 高级推理模式
- ✅ 多 Agent 协作与编排
- ✅ 生产级基础设施：日志、缓存、断路器、指标

**今天，我们正式进入 Phase 4: RAG 实战。** Agent 需要"知识"才能做出准确回答，RAG 就是给 Agent 装上一个"外部知识库"。

---

## 📚 新知识讲解

### 1. 什么是 RAG？

**比喻**：LLM 是一个"闭卷考试"的学霸——只能靠训练记忆回答。RAG 是给学霸一本"开卷参考书"——先查书再回答。

```
用户: "Python 3.12 有什么新特性？"
         │
         ▼
┌─────────────────────────────────────┐
│  RAG 三段式架构                       │
│                                      │
│  ① Indexing（索引）                   │
│     文档 → 分块 → 嵌入向量 → 向量库    │
│                                      │
│  ② Retrieval（检索）                  │
│     查询 → 嵌入向量 → 相似度搜索 → Top-K│
│                                      │
│  ③ Generation（生成）                 │
│     检索结果 + 查询 → LLM → 答案       │
└─────────────────────────────────────┘
```

### 2. Embedding — 文本到向量的魔法

Embedding 将任意文本映射为一个固定维度的浮点数向量（如 768 维）：

```
"Python 编程" → [0.12, -0.34, 0.56, ..., 0.23] (768个数字)
"Java 编程"   → [0.15, -0.30, 0.52, ..., 0.21] (768个数字)
"今天天气"    → [-0.45, 0.67, -0.12, ..., 0.88] (768个数字)
```

**核心规律**：语义相近的文本 → 向量距离近。

余弦相似度衡量两个向量的"方向一致性"：
```python
def cos_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

代码见 [embedding_demo.py](embedding_demo.py)。

### 3. ChromaDB — 向量数据库

ChromaDB 是 RAG 系统最常用的开源向量数据库：

```python
import chromadb

# 创建客户端和 Collection
client = chromadb.PersistentClient(path="./my_db")
collection = client.get_or_create_collection(name="my_docs")

# 添加文档（自动嵌入）
collection.add(documents=["Python 是一门编程语言"], ids=["doc_1"])

# 语义搜索
results = collection.query(query_texts=["编程语言有哪些？"], n_results=3)
```

代码见 [chromadb_demo.py](chromadb_demo.py)。

### 4. 构建第一个 RAG 系统

见 [rag_basics.py](rag_basics.py) — `RAGSystem` 类整合了完整的三段式流程：

```python
rag = RAGSystem()
rag.index_documents(["Python 是...", "机器学习是...", "深度学习是..."])
result = rag.query("什么是机器学习？")
# → 检索相关文档 → LLM 基于文档生成答案
```

### 5. 关键注意点

- `HF_ENDPOINT` 环境变量：必须在导入 `sentence_transformers` 之前设置
- 嵌入模型选择：`BAAI/bge-small-zh-v1.5` 是中文优化的小模型（768维）
- ChromaDB 使用原生 SDK（`chromadb`），不是 LangChain 的包装器

---

## 💡 实例演示

完整演示见 [example.py](example.py)，包含三个环节：

1. **Embedding 演示** — 加载模型、计算向量、相似度比较
2. **ChromaDB 演示** — 创建 Collection、添加文档、语义搜索
3. **RAG 系统演示** — 完整的索引→检索→生成流程

**运行方法：**
```bash
cd phase4_rag/day16_rag_basics
pip install -r requirements.txt
python example.py
```

---

## ✍️ 练习题

### 练习1：基础题
1. 运行 `python example.py`，观察嵌入向量的维度和相似度计算结果
2. 修改 `DEMO_DOCUMENTS` 添加 3 篇自己的文档，重新运行 RAG 查询
3. 在 ChromaDB demo 中使用 `where` 参数过滤元数据

### 练习2：进阶题
1. 实现"最大边际相关性（MMR）"重排序：在保证相关性的同时增加结果多样性
2. 在 `RAGSystem` 中添加"来源引用"：生成的答案标注来自哪篇文档
3. 对比不同 embedding 模型的检索效果（如 `bge-base-zh-v1.5` vs `bge-small-zh-v1.5`）

### 练习3：挑战题
1. 实现一个"文档更新"机制：修改某篇文档后，增量更新向量库（而非重建整个索引）
2. 实现"多 Collection 联合检索"：同时从不同知识库检索并合并结果

---

## 🔮 后一天知识展望

今天我们了解了 RAG 的基本架构，但文档在入库前需要经过**分块处理**。明天（Day17）我们将学习文档加载和分块策略——固定大小分块、句子边界分块、滑动窗口分块，以及如何构建一个从原始文档到可查询知识库的完整 RAG 构建器。

---

## 📝 今日总结

- ✅ RAG = Indexing（索引）+ Retrieval（检索）+ Generation（生成）
- ✅ Embedding 将文本映射为向量，语义相近的文本向量距离近
- ✅ ChromaDB 是 RAG 系统常用的开源向量数据库（原生 SDK，零 LangChain）
- ✅ 余弦相似度 `cos(a,b) = dot(a,b) / (|a|*|b|)` 是最常用的向量相似度度量
- ✅ `BAAI/bge-small-zh-v1.5` 是中文优化的轻量嵌入模型
- ✅ `HF_ENDPOINT` 必须在导入 sentence-transformers 之前设置

---

## 🚀 下一步

1. 完成所有练习题
2. 理解 ChromaDB 的 `collection.query()` 返回结构
3. 思考：为什么 RAG 能"减少模型幻觉"？

---

## 📖 参考资料

- [ChromaDB 官方文档](https://docs.trychroma.com/)
- [BGE (BAAI General Embedding) 模型](https://huggingface.co/BAAI/bge-small-zh-v1.5)
- [sentence-transformers 文档](https://www.sbert.net/)
- [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)
