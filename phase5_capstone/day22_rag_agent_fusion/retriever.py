"""
retriever.py — Day 22 RAG 检索器模块

为 Agent 提供知识检索能力的核心模块。支持：
1. 向量检索（语义匹配）— 通过 sentence-transformers 嵌入 + ChromaDB
2. BM25 检索（关键词匹配）— 通过 rank_bm25 + jieba 分词
3. 混合检索（RRF 融合）— 取两者之长

Agent 将 RAGRetriever.search() 作为工具调用，
检索结果注入 LLM 上下文，实现"检索增强对话"。

设计原则：独立模块，与 Agent 解耦，可单独测试。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import HF_ENDPOINT, EMBEDDING_MODEL, EMBEDDING_DEVICE

import os
os.environ["HF_ENDPOINT"] = HF_ENDPOINT

import json
from typing import List, Optional, Dict, Any
import numpy as np

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import jieba

from models import RAGResult

# ==================== RRF 融合常量 ====================
RRF_K = 60  # RRF 平滑参数，取值越大各列表权重越均匀

# ==================== 演示知识库文档 ====================
DEMO_DOCUMENTS: List[Dict[str, str]] = [
    {"content": "人工智能（AI）是计算机科学的一个分支，旨在创建能够模拟人类智能的系统。AI 包括机器学习、深度学习、自然语言处理等多个子领域。2022 年 ChatGPT 的发布标志着 AI 进入大众化时代。", "source": "ai_intro.md"},
    {"content": "RAG（检索增强生成，Retrieval-Augmented Generation）是一种结合信息检索与文本生成的 AI 架构。它先从知识库中检索相关文档，再将文档作为上下文提供给 LLM 生成答案，有效减少幻觉。", "source": "rag_basics.md"},
    {"content": "向量数据库是专门用于存储和检索高维向量数据的数据库系统。常见的向量数据库包括 ChromaDB、Milvus、Pinecone 等。ChromaDB 轻量易用，适合中小规模 RAG 场景。", "source": "vector_db.md"},
    {"content": "文本嵌入（Text Embedding）是将文本转换为固定维度向量的技术。语义相似的文本在向量空间中距离更近。常用的嵌入模型有 BGE、M3E、text2vec 等。", "source": "embedding.md"},
    {"content": "BM25（Best Matching 25）是一种基于概率检索模型的排序函数，在搜索引擎中广泛使用。它通过词频（TF）和逆文档频率（IDF）计算查询与文档的相关性。", "source": "bm25.md"},
    {"content": "混合检索（Hybrid Retrieval）融合稀疏检索（如 BM25）和稠密检索（如向量相似度）的优势。RRF（倒数排名融合）是最常用的融合算法，无需训练即可有效合并排序结果。", "source": "hybrid_search.md"},
    {"content": "Agent 是能够自主感知环境、做出决策并执行行动的 AI 系统。ReAct（推理+行动）模式是最经典的 Agent 架构，通过交替进行思考（Thought）和行动（Action）来完成任务。", "source": "agent.md"},
    {"content": "MCP（Model Context Protocol）是由 Anthropic 提出的 AI 与工具之间的标准化通信协议。它基于 JSON-RPC 2.0，定义了 Host、Client、Server 三层架构，实现了工具的跨框架复用。", "source": "mcp.md"},
    {"content": "分块策略（Chunking Strategy）是 RAG 系统的基础。常见策略包括固定大小分块、语义分块、递归分块。合理的分块大小（通常 256-1024 tokens）能显著提升检索准确性。", "source": "chunking.md"},
    {"content": "重排序（Re-ranking）是检索后处理步骤，通过更精确的模型对初步检索结果进行重新排序。Cross-Encoder 重排序器虽然速度较慢，但准确率远高于双编码器。", "source": "rerank.md"},
    {"content": "大语言模型（LLM）是深度学习在 NLP 领域的突破性应用。GPT 系列、Claude 系列、DeepSeek 系列是目前主流的 LLM。LLM 通过自回归方式逐 token 生成文本。", "source": "llm.md"},
    {"content": "Function Calling 允许 LLM 调用外部工具和 API。开发者定义工具的 JSON Schema，LLM 根据用户意图决定是否调用工具及传递什么参数，是实现 Agent 的核心能力。", "source": "function_calling.md"},
    {"content": "多轮对话管理是构建对话系统的关键挑战。需要维护对话历史、理解上下文引用、处理话题切换。常见策略包括滑动窗口、摘要压缩、混合记忆等。", "source": "dialogue.md"},
    {"content": "Python 是 AI 开发的首选语言，拥有丰富的生态：NumPy（数值计算）、Pandas（数据处理）、PyTorch（深度学习）、LangChain（LLM 应用框架）等。", "source": "python.md"},
    {"content": "ChromaDB 是一个开源的向量数据库，专为 RAG 应用设计。它支持内存模式和持久化模式，内置多种距离度量（余弦相似度、欧氏距离等），并提供了简洁的 Python API。", "source": "chromadb.md"},
]


class RAGRetriever:
    """RAG 检索器 — 为 Agent 提供知识检索能力

    架构：
    1. BM25 索引（稀疏检索）→ 关键词精准匹配
    2. ChromaDB 向量索引（稠密检索）→ 语义理解匹配
    3. RRF 融合 → 综合排序

    Agent 将此检索器包装为 MCP 工具，供 LLM 调用。
    """

    def __init__(self, collection_name: str = "rag_agent_kb"):
        """初始化检索器 — 加载模型、构建索引

        Args:
            collection_name: ChromaDB 集合名称
        """
        # 加载嵌入模型（已通过 HF_ENDPOINT 设置镜像）
        self.embedding_model = SentenceTransformer(
            EMBEDDING_MODEL, device=EMBEDDING_DEVICE
        )

        # 初始化 ChromaDB 客户端（内存模式，演示用）
        self.chroma_client = chromadb.Client(
            ChromaSettings(anonymized_telemetry=False)
        )
        # 如果集合已存在则删除重建（演示模式）
        try:
            self.chroma_client.delete_collection(collection_name)
        except Exception:
            pass
        self.collection = self.chroma_client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # 余弦相似度
        )

        # BM25 索引（延迟构建）
        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[Dict[str, str]] = []
        self._indexed = False

    def index(self, documents: List[Dict[str, str]] = None):
        """构建索引 — 将文档同时写入 ChromaDB 和 BM25

        Args:
            documents: 文档列表 [{"content": "...", "source": "..."}]
        """
        docs = documents or DEMO_DOCUMENTS
        self.documents = docs

        contents = [d["content"] for d in docs]

        # 1. 向量索引（ChromaDB）
        embeddings = self.embedding_model.encode(contents).tolist()
        self.collection.add(
            ids=[f"doc_{i}" for i in range(len(contents))],
            embeddings=embeddings,
            documents=contents,
            metadatas=[{"source": d["source"]} for d in docs],
        )

        # 2. BM25 索引（jieba 分词）
        tokenized = [list(jieba.cut(content)) for content in contents]
        self.bm25 = BM25Okapi(tokenized)
        self._indexed = True
        print(f"  ✅ 索引进阶完成: {len(contents)} 篇文档（ChromaDB + BM25）")

    def _vector_search(self, query: str, top_k: int = 5) -> List[RAGResult]:
        """向量检索 — 语义相似度匹配"""
        query_embedding = self.embedding_model.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding, n_results=top_k
        )
        rag_results = []
        for i in range(len(results["ids"][0])):
            rag_results.append(RAGResult(
                content=results["documents"][0][i],
                source=results["metadatas"][0][i].get("source", ""),
                score=1.0 - results["distances"][0][i] if results["distances"] else 0.0,
            ))
        return rag_results

    def _bm25_search(self, query: str, top_k: int = 5) -> List[RAGResult]:
        """BM25 检索 — 关键词精准匹配"""
        if not self.bm25:
            return []
        tokenized_query = list(jieba.cut(query))
        scores = self.bm25.get_scores(tokenized_query)
        # 获取 top_k 索引
        top_indices = np.argsort(scores)[::-1][:top_k]
        rag_results = []
        for idx in top_indices:
            if scores[idx] > 0:
                rag_results.append(RAGResult(
                    content=self.documents[idx]["content"],
                    source=self.documents[idx]["source"],
                    score=float(scores[idx]),
                ))
        return rag_results

    def _rrf_fusion(
        self,
        vec_results: List[RAGResult],
        bm25_results: List[RAGResult],
        top_k: int = 5
    ) -> List[RAGResult]:
        """RRF 融合 — 倒数排名融合算法

        公式：RRF_score(d) = Σ 1/(k + rank_i(d))
        其中 k=60（平滑参数），rank_i(d) 是文档 d 在第 i 个排序列表中的排名。

        RRF 的优势：无需训练、处理任意数量的排序列表、各列表贡献均衡。
        """
        # 构建 文档内容 → 融合分数 的映射
        scores: Dict[str, float] = {}
        doc_map: Dict[str, RAGResult] = {}

        # 向量检索排名
        for rank, result in enumerate(vec_results, start=1):
            rrf = 1.0 / (RRF_K + rank)
            scores[result.content] = scores.get(result.content, 0.0) + rrf
            doc_map[result.content] = result

        # BM25 检索排名
        for rank, result in enumerate(bm25_results, start=1):
            rrf = 1.0 / (RRF_K + rank)
            scores[result.content] = scores.get(result.content, 0.0) + rrf
            if result.content not in doc_map:
                doc_map[result.content] = result

        # 按融合分数降序排列
        sorted_contents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        fused = []
        for content, score in sorted_contents[:top_k]:
            result = doc_map[content]
            result.score = round(score, 4)
            fused.append(result)
        return fused

    def search(self, query: str, top_k: int = 3,
               use_hybrid: bool = True) -> List[RAGResult]:
        """执行检索 — Agent 的核心工具

        Args:
            query: 查询文本
            top_k: 返回结果数
            use_hybrid: 是否启用混合检索（默认开启）

        Returns:
            RAGResult 列表，按相关性降序排列
        """
        if not self._indexed:
            self.index()

        if use_hybrid:
            vec_results = self._vector_search(query, top_k * 2)
            bm25_results = self._bm25_search(query, top_k * 2)
            return self._rrf_fusion(vec_results, bm25_results, top_k)
        else:
            return self._vector_search(query, top_k)

    def format_for_llm(self, results: List[RAGResult]) -> str:
        """将检索结果格式化为 LLM 可读的文本

        Args:
            results: RAG 检索结果列表

        Returns:
            格式化的文本，可直接注入 LLM 对话上下文
        """
        if not results:
            return "（未找到相关文档）"

        parts = ["【检索到的知识库内容】\n"]
        for i, result in enumerate(results, 1):
            parts.append(f"[{i}] (来源: {result.source}, 相关度: {result.score})\n{result.content}\n")
        return "\n".join(parts)

    @property
    def stats(self) -> Dict[str, Any]:
        """检索器统计信息"""
        return {
            "indexed": self._indexed,
            "document_count": len(self.documents),
            "embedding_model": EMBEDDING_MODEL,
            "collection_name": self.collection.name if self.collection else "",
        }
