"""
rag_basics.py — 从零构建 RAG 系统（检索增强生成）

RAG 三段式架构：
1. 索引（Indexing）— 文档分块 → 嵌入 → 存入向量库
2. 检索（Retrieval）— 查询嵌入 → 相似度搜索 → 取 Top-K
3. 生成（Generation）— 检索结果注入 Prompt → LLM 生成答案

设计原则：
- ChromaDB 原生 SDK（非 LangChain 封装）
- 嵌入模型独立注入
- openai SDK 驱动生成
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
from typing import List


class CustomEmbedding:
    """自定义嵌入函数 — 封装 SentenceTransformer"""

    def __init__(self, model_name="BAAI/bge-small-zh-v1.5"):
        self.model = SentenceTransformer(model_name)

    def __call__(self, texts):
        return self.model.encode(texts).tolist()


class RAGSystem:
    """从零构建的 RAG 系统 — 检索增强生成"""

    def __init__(self, db_path: str = None, collection_name: str = "rag_demo"):
        # 嵌入模型
        self.embed_fn = CustomEmbedding()

        # ChromaDB 客户端
        db_path = db_path or str(Path(__file__).parent / "chroma_rag")
        self.client = chromadb.PersistentClient(path=db_path)

        # 获取或创建 Collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embed_fn
        )

        # LLM 客户端
        self.llm = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

        print(f"  ✅ RAG 系统初始化完成")
        print(f"  📦 Collection: {collection_name}")
        print(f"  📄 当前文档数: {self.collection.count()}")

    def index_documents(self, documents: List[str],
                        metadatas: List[dict] = None,
                        ids: List[str] = None) -> None:
        """索引阶段：将文档嵌入后存入向量库"""
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]

        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"  ✅ 索引完成：添加 {len(documents)} 篇文档，当前总数 {self.collection.count()}")

    def retrieve(self, query: str, top_k: int = 3) -> list:
        """检索阶段：按相似度搜索最相关的文档"""
        results = self.collection.query(query_texts=[query], n_results=top_k)
        docs = []
        for i, (doc, distance) in enumerate(zip(results["documents"][0], results["distances"][0])):
            docs.append({"content": doc, "score": 1.0 - distance, "rank": i + 1})
        return docs

    def generate(self, query: str, context_docs: list) -> str:
        """生成阶段：基于检索到的文档生成答案"""
        # 构建上下文
        context_text = "\n\n".join([
            f"[文档{d['rank']}] {d['content']}"
            for d in context_docs
        ])

        system_prompt = (
            "你是一个基于知识库的问答助手。请仅根据提供的文档内容回答问题。\n"
            "如果文档中没有相关信息，请明确告知用户'现有资料中未找到相关信息'。\n"
            "回答时引用具体的文档编号。"
        )

        response = self.llm.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"参考资料：\n{context_text}\n\n问题：{query}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content or "无法生成答案"

    def query(self, query: str, top_k: int = 3) -> dict:
        """完整 RAG 查询流程：检索 + 生成"""
        print(f"\n  🔍 查询: '{query}'")

        # 步骤 1：检索
        docs = self.retrieve(query, top_k=top_k)
        print(f"  📚 检索到 {len(docs)} 篇相关文档:")
        for d in docs:
            print(f"    [{d['rank']}] 相似度={d['score']:.4f}: {d['content'][:80]}...")

        # 步骤 2：生成
        answer = self.generate(query, docs)
        return {"query": query, "retrieved_docs": docs, "answer": answer}

    def clear(self) -> None:
        """清空 Collection"""
        self.client.delete_collection(self.collection.name)
        print("  🧹 Collection 已清空")


def main():
    """主函数 — 演示完整 RAG 流程"""
    print("=" * 60)
    print("  RAG 系统演示 — 检索增强生成")
    print("=" * 60)

    # 知识库文档（模拟企业知识库）
    documents = [
        "Python 是由 Guido van Rossum 于 1991 年创建的高级编程语言。它的设计哲学强调代码可读性和简洁语法。",
        "Java 由 James Gosling 于 1995 年在 Sun Microsystems 创建。它是一种面向对象的编程语言，以'一次编写，到处运行'著称。",
        "深度学习是机器学习的一个分支，使用多层人工神经网络。2012 年 AlexNet 赢得 ImageNet 竞赛后，深度学习进入爆发期。",
        "CNN（卷积神经网络）主要用于图像识别和处理。它通过卷积层提取特征，池化层降低维度。",
        "RNN（循环神经网络）适合处理序列数据，如文本和时间序列。LSTM 和 GRU 解决了长序列的梯度消失问题。",
        "Transformer 由 Google 在 2017 年提出，彻底改变了 NLP 领域。它基于自注意力机制，并行计算能力强。",
        "BERT 是 Google 2018 年发布的预训练语言模型，采用双向 Transformer 编码器架构，在下游任务中表现优异。",
        "GPT 系列由 OpenAI 开发，GPT-3 有 1750 亿参数。GPT-4 于 2023 年发布，支持多模态输入。",
        "ChromaDB 是开源的向量数据库，专为 AI 应用设计。支持嵌入式存储、元数据过滤和相似度搜索。",
        "RAG（检索增强生成）将信息检索和文本生成结合，先检索相关文档，再交给 LLM 生成答案，降低了模型幻觉。",
    ]

    try:
        rag = RAGSystem()

        # 索引文档
        rag.index_documents(documents)

        # 查询测试
        queries = [
            "Python 是谁创建的？",
            "Transformer 架构有什么特点？",
            "什么是 RAG 技术？",
        ]

        for query in queries:
            try:
                result = rag.query(query)
                print(f"\n  🤖 回答: {result['answer']}")
            except Exception as e:
                print(f"  ⚠️ LLM 调用失败: {e}")

        # 清理
        rag.clear()
        print("\n✅ RAG 演示完成！")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
