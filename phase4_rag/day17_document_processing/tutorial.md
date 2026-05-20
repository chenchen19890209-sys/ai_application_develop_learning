# Day 17: 文档处理与基础 RAG

> 🎯 **学习目标**
>
> - 掌握多种格式文档的加载方法（TXT、Markdown、Python 代码）
> - 理解并实现三种核心分块策略：固定大小 / 句子边界 / 滑动窗口
> - 理解 chunk_overlap 的作用：保证上下文连续性
> - 掌握元数据管理：随文档块存储来源、索引、字符数等信息
> - 构建完整的 RAG Builder：从原始文档到可查询知识库的一站式流程

---

## 📖 前一天知识回顾

昨天（Day16）我们学习了 RAG 的基本架构：
- ✅ Embedding 原理和 ChromaDB 原生操作
- ✅ 第一个 RAGSystem：索引→检索→生成

**问题：** Day16 的 `RAGSystem.index_documents()` 直接接收已处理好的"文档列表"。但现实中，我们面对的是**原始文件**（TXT/MD/PY），需要先加载、分块、再入向量库。

**今天，我们处理 RAG 的前置环节：文档处理！**

---

## 📚 新知识讲解

### 1. 文档处理在 RAG 中的位置

```
原始文件(.txt/.md/.py) → [文档加载] → 长文本 → [分块] → 文档块 → [嵌入] → 向量库
                                    ↑ 今天的内容 ↑
```

### 2. 文档加载器 — TextLoader

见 [document_loader.py](document_loader.py) — `TextLoader` 类：

```python
class TextLoader:
    @staticmethod
    def load(file_path: str) -> str:
        """加载任意文本文件，自动处理 UTF-8 编码"""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def load_python(file_path: str) -> str:
        """加载 Python 文件（可选择性去注释）"""
        ...
```

设计理念：**零 LangChain 依赖，纯 Python 标准库实现**。

### 3. 分块策略 — DocumentChunker

见 [document_loader.py](document_loader.py) — `DocumentChunker` 类。为什么需要分块？

- LLM 的上下文窗口有限（虽然越来越大，但检索精度会随文本增长而下降）
- 更小的块 → 更精准的检索结果
- 但太小的块 → 丢失上下文

#### 策略 1：固定大小分块

```python
def chunk_by_fixed_size(self, text: str) -> List[str]:
    # 每 chunk_size 个字符切一块，块间重叠 chunk_overlap 个字符
    # 简单但可能在句子中间切断
```

```
原文: "今天天气很好。我们去公园。"
固定分块(size=8, overlap=2):
  块0: "今天天气很好。"
  块1: "。我们去公园。"
```

#### 策略 2：句子边界分块（推荐）

```python
def chunk_by_sentence(self, text: str) -> List[str]:
    # 按 。！？\n 分隔符切分，中文友好
    # 尽量保证每块在完整句子边界结束
```

**比喻**：固定分块像用菜刀切菜——不管纤维走向，一刀下去；句子分块像顺着纹理切——保持自然边界。

#### 策略 3：滑动窗口分块

```python
def chunk_by_sliding_window(self, text: str) -> List[str]:
    # step = chunk_size - chunk_overlap
    # 每步移动 step 个字符
```

### 4. chunk_overlap 的作用

```
chunk_overlap = 50

块 0: "...递归神经网络（RNN）适合处理序列数据。"
块 1: "适合处理序列数据。2017年，Google提出了..."  ← 重叠部分保证语义不丢失

如果 overlap=0：
块 0: "...递归神经网络（RNN）适合处理序列数据。"
块 1: "2017年，Google提出了..."  ← "谁适合处理序列数据？RNN"，但块1没有这个信息！
```

### 5. 附带元数据的分块

```python
chunks = chunker.chunk_with_metadata(text, source="ai_overview.txt", strategy="sentence")
# 每个块附带: {"source": "...", "chunk_index": 0, "total_chunks": 5, "char_count": 145}
```

元数据在检索时非常重要——用户不仅想知道"答案是什么"，还想知道"答案来自哪篇文档"。

### 6. RAGBuilder — 一站式构建器

见 [build_rag.py](build_rag.py) — `RAGBuilder` 类：

```python
builder = RAGBuilder()
builder.add_document(text="Python 是...", source="python_intro")
builder.add_documents({"doc1": "...", "doc2": "..."})
result = builder.query("Python 是什么时候创建的？")
```

`RAGBuilder` 内部自动完成：分块 → 嵌入 → 存入 ChromaDB → 提供 search/generate/query 接口。

---

## 💡 实例演示

### 实例1：三种分块策略对比

```python
from document_loader import DocumentChunker
chunker = DocumentChunker(chunk_size=150, chunk_overlap=30)

# 固定大小分块
chunks = chunker.chunk_by_fixed_size(sample_text)

# 句子边界分块
chunks = chunker.chunk_by_sentence(sample_text)

# 带元数据分块（生产推荐）
results = chunker.chunk_with_metadata(sample_text, source="ai_overview.txt")
```

### 实例2：完整 RAG 构建

```python
from build_rag import RAGBuilder
builder = RAGBuilder()
builder.add_documents({"python_intro": "...", "ai_overview": "...", "rag_tech": "..."})
result = builder.query("RAG 的工作流程是什么？")
```

**运行方法：**
```bash
cd phase4_rag/day17_document_processing
python example.py
```

---

## ✍️ 练习题

### 练习1：基础题
1. 运行 `python example.py`，观察三种分块策略的差异
2. 修改 `chunk_size` 参数（从 150 改成 300），观察分块结果的变化
3. 创建一个自定义的 txt 文件并用 `TextLoader.load()` 加载

### 练习2：进阶题
1. 实现"递归分块"策略：优先按段落(\\n\\n)切分，超长段落再按句子切分
2. 给 `DocumentChunker` 添加"中文分句"功能：使用 `re.split(r'(?<=[。！？])\s*', text)` 更准确的中文分句
3. 给 `RAGBuilder` 添加 `delete_document(source_name)` 方法：删除某个来源的所有块

### 练习3：挑战题
1. 实现"自适应分块"：根据文档内容语义自动决定最佳 chunk_size（如通过检测段落长度分布）
2. 实现"层级分块"：大块（parent chunk）+ 小块（child chunk），检索时先找小块再取大块获取上下文

---

## 🔮 后一天知识展望

有了文档分块和基础 RAG，下一步是**提升检索质量**。明天（Day18）我们将学习检索优化：BM25 关键字检索 + 向量语义检索 → RRF 混合融合 + CrossEncoder 重排序→LLM 精排。让检索从"能找到"进化到"找得准"！

---

## 📝 今日总结

- ✅ 文档加载 → 分块 → 嵌入 → 向量库，是 RAG 的完整前置流程
- ✅ 句子边界分块最适合中文场景（在自然断点切分）
- ✅ chunk_overlap 保证上下文不丢失（相邻块共享内容）
- ✅ 元数据（source、chunk_index）随块存储，便于检索时来源追溯
- ✅ RAGBuilder 提供 add/search/generate/query 一站式接口
- ✅ 所有实现零 LangChain 依赖

---

## 🚀 下一步

1. 完成所有练习题
2. 尝试用 `RAGBuilder` 索引你自己的文档
3. 思考：如果文档包含图片/表格，分块策略需要如何调整？

---

## 📖 参考资料

- [Chunking Strategies for RAG (Pinecone)](https://www.pinecone.io/learn/chunking-strategies/)
- [ChromaDB Usage Guide](https://docs.trychroma.com/usage-guide)
- [sentence-transformers 文档](https://www.sbert.net/)
- [Building RAG-based Chatbots (Anthropic)](https://docs.anthropic.com/en/docs/build-with-claude/embeddings)
