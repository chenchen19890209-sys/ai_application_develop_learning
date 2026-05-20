"""
build_rag.py — 从文档构建可用的 RAG 系统

功能：
1. 加载多篇文档 → 分块 → 嵌入 → 存入 ChromaDB
2. 支持增量索引和更新
3. 完整的查询接口（检索 + 生成）

设计原则：目录式管理文档，一键构建 RAG 知识库
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, HF_ENDPOINT

import os
os.environ["HF_ENDPOINT"] = HF_ENDPOINT if HF_ENDPOINT else "https://hf-mirror.com"

import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from document_loader import DocumentChunker
from typing import List, Dict


class CustomEmbedding:
    """自定义嵌入函数"""

    def __init__(self, model_name="BAAI/bge-small-zh-v1.5"):
        self.model = SentenceTransformer(model_name)

    def __call__(self, texts):
        return self.model.encode(texts).tolist()


class RAGBuilder:
    """RAG 系统构建器 — 从文档到可查询的知识库"""

    def __init__(self, collection_name: str = "knowledge_base",
                 chunk_size: int = 300, chunk_overlap: int = 50):
        # 嵌入函数
        self.embed_fn = CustomEmbedding()

        # ChromaDB 客户端
        db_path = str(Path(__file__).parent / "rag_db")
        self.client = chromadb.PersistentClient(path=db_path)

        # Collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embed_fn
        )

        # 分块器
        self.chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # LLM 客户端
        self.llm = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

        print(f"  ✅ RAG Builder 初始化")
        print(f"  📦 Collection: {collection_name}, 当前文档数: {self.collection.count()}")

    def add_document(self, text: str, source: str = "unknown") -> int:
        """添加单篇文档 — 自动分块并索引"""
        chunks = self.chunker.chunk_with_metadata(text, source=source, strategy="sentence")
        if not chunks:
            return 0

        # 准备 ChromaDB 数据
        documents = [c["content"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        ids = [f"{source}_chunk_{c['metadata']['chunk_index']}" for c in chunks]

        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"  ✅ 索引完成: '{source}' → {len(chunks)} 个块")
        return len(chunks)

    def add_documents(self, doc_map: Dict[str, str]) -> int:
        """批量添加文档"""
        total = 0
        for source, text in doc_map.items():
            total += self.add_document(text, source=source)
        print(f"  ✅ 共索引 {len(doc_map)} 篇文档, {total} 个块, 总数 {self.collection.count()}")
        return total

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """检索相关文档块"""
        results = self.collection.query(query_texts=[query], n_results=top_k)
        docs = []
        for i, (doc, distance, meta) in enumerate(zip(
            results["documents"][0], results["distances"][0], results["metadatas"][0]
        )):
            docs.append({
                "content": doc,
                "score": round(1.0 - distance, 4),
                "source": meta.get("source", "unknown"),
                "chunk_index": meta.get("chunk_index", 0),
            })
        return docs

    def generate(self, query: str, docs: list) -> str:
        """基于检索结果生成回答"""
        context = "\n\n---\n".join([
            f"[来源: {d['source']}] {d['content']}" for d in docs
        ])

        response = self.llm.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": (
                    "你是一个知识库问答助手。只基于提供的文档内容回答问题。"
                    "如果文档中没有答案，直接说'现有资料未覆盖此问题'。"
                    "引用具体的来源。"
                )},
                {"role": "user", "content": f"参考资料：\n{context}\n\n问题：{query}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content or "无法生成答案"

    def query(self, query: str, top_k: int = 5) -> dict:
        """完整 RAG 查询"""
        print(f"\n  🔍 '{query}'")
        docs = self.search(query, top_k=top_k)
        print(f"  📚 检索到 {len(docs)} 篇相关文档段")
        for d in docs:
            print(f"    [{d['score']:.4f}] {d['source']}: {d['content'][:60]}...")

        answer = self.generate(query, docs)
        return {"query": query, "docs": docs, "answer": answer}


def main():
    """演示：构建知识库 + 查询"""
    print("=" * 60)
    print("  RAG 构建器演示")
    print("=" * 60)

    # 知识库文档
    doc_map = {
        "python_intro": (
            "Python 由 Guido van Rossum 于 1991 年创建。它是一种解释型、面向对象的高级编程语言。"
            "Python 的设计哲学强调代码可读性和简洁语法。它的名字来源于英国喜剧团体 Monty Python。"
            "Python 3.0 于 2008 年发布，带来了一些重大改进。最新版本 Python 3.12 于 2023 年发布。"
        ),
        "ai_overview": (
            "人工智能（AI）是计算机科学的分支，旨在创造能执行需要人类智能的任务的系统。"
            "AI 的三大要素是：数据、算法、算力。主要子领域包括机器学习、深度学习、NLP、计算机视觉。"
            "2022 年底 ChatGPT 的发布引爆了 AI 应用的新浪潮。大语言模型（LLM）成为 AI 的核心技术。"
            "Transformer 架构是 LLM 的基础，自 2017 年被提出以来彻底改变了 NLP 领域。"
        ),
        "rag_tech": (
            "RAG（检索增强生成）结合了信息检索和文本生成两种技术。它的工作流程是："
            "1. 索引：将文档分块嵌入存入向量数据库；2. 检索：查询时搜索最相关的文档块；"
            "3. 生成：将检索到的文档作为上下文提供给 LLM 生成答案。"
            "RAG 的主要优势：减少模型幻觉、利用最新知识、可溯源、成本低（无需微调模型）。"
            "ChromaDB 是 RAG 系统常用的开源向量数据库，支持元数据过滤和高效相似度搜索。"
        ),
    }

    try:
        builder = RAGBuilder()

        # 索引文档
        builder.add_documents(doc_map)

        # 测试查询
        test_queries = [
            "Python 是什么时候创建的？",
            "AI 的核心要素有哪些？",
            "RAG 的工作流程是什么？",
        ]

        for q in test_queries:
            try:
                result = builder.query(q)
                print(f"  🤖 回答: {result['answer']}\n")
            except Exception as e:
                print(f"  ⚠️ LLM 调用失败: {e}")

        # 清理
        builder.client.delete_collection(builder.collection.name)
        print("✅ 演示完成")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
