"""
chromadb_demo.py — ChromaDB 向量数据库原生操作

功能：
1. 创建 Collection（向量集合）
2. 添加文档（自动嵌入 + 存储）
3. 相似度搜索（向量检索）
4. 元数据过滤（混合搜索）

设计原则：
- 使用 ChromaDB 原生 SDK（非 LangChain 封装）
- 嵌入函数直接注入，清晰可见
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import HF_ENDPOINT

import os
os.environ["HF_ENDPOINT"] = HF_ENDPOINT if HF_ENDPOINT else "https://hf-mirror.com"

import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer


class CustomEmbeddingFunction:
    """自定义嵌入函数 — 封装 SentenceTransformer，注入 ChromaDB"""

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5"):
        self.model = SentenceTransformer(model_name)

    def __call__(self, input):
        """ChromaDB 调用接口 — 接收文本列表，返回嵌入列表"""
        return self.model.encode(input).tolist()


def demo_chromadb_basics():
    """演示 1：ChromaDB 基础操作"""
    print("=" * 60)
    print("  ChromaDB 基础 — Collection 的增删查")
    print("=" * 60)

    # 创建 ChromaDB 客户端（持久化模式）
    db_path = str(Path(__file__).parent / "chroma_db")
    client = chromadb.PersistentClient(path=db_path)

    # 创建嵌入函数
    embed_fn = CustomEmbeddingFunction()

    # 创建或获取 Collection
    collection = client.get_or_create_collection(
        name="demo_collection",
        embedding_function=embed_fn,
        metadata={"description": "Day 16 演示集合"}
    )

    print(f"  📦 Collection: {collection.name}")
    print(f"  当前文档数: {collection.count()}")

    # 添加文档
    documents = [
        "Python 是一种解释型、面向对象的高级编程语言",
        "深度学习是机器学习的一个子集，使用多层神经网络",
        "ChromaDB 是一个开源的向量数据库",
        "RAG 结合了信息检索和文本生成技术",
        "MCP 协议实现了 AI 与工具的标准化通信",
    ]
    ids = [f"doc_{i}" for i in range(len(documents))]

    collection.add(documents=documents, ids=ids)
    print(f"  ✅ 添加 {len(documents)} 篇文档后，总数: {collection.count()}")

    return collection


def demo_similarity_search(collection):
    """演示 2：向量相似度搜索"""
    print("\n" + "=" * 60)
    print("  相似度搜索 — 检索最相关的文档")
    print("=" * 60)

    queries = [
        "编程语言有哪些",
        "机器学习和深度学习的关系",
        "数据库技术",
    ]

    for query in queries:
        print(f"\n  🔍 查询: '{query}'")
        results = collection.query(query_texts=[query], n_results=2)
        print(f"  结果:")
        for i, (doc, distance) in enumerate(zip(results["documents"][0], results["distances"][0])):
            print(f"    {i+1}. [{distance:.4f}] {doc[:80]}...")


def demo_metadata_filter(collection):
    """演示 3：元数据过滤 — 精确匹配 + 相似度搜索"""
    print("\n" + "=" * 60)
    print("  元数据过滤")
    print("=" * 60)

    # 添加带元数据的文档
    tagged_docs = [
        ("Python 装饰器详解 — 实现函数增强的技术", {"category": "programming", "level": "advanced"}),
        ("Python 基础语法 — 变量、条件和循环", {"category": "programming", "level": "beginner"}),
        ("深度神经网络训练技巧 — 梯度下降和反向传播", {"category": "ai", "level": "advanced"}),
        ("AI 入门 — 什么是人工智能", {"category": "ai", "level": "beginner"}),
    ]

    ids = [f"tagged_{i}" for i in range(len(tagged_docs))]
    documents = [d[0] for d in tagged_docs]
    metadatas = [d[1] for d in tagged_docs]

    collection.add(documents=documents, metadatas=metadatas, ids=ids)

    # 查询 + 元数据过滤
    print(f"\n  🔍 查询: '编程'，过滤: level=beginner")
    results = collection.query(
        query_texts=["编程"],
        n_results=2,
        where={"level": "beginner"}
    )
    for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
        print(f"    {i+1}. {doc[:80]}... | meta={meta}")

    print(f"\n  🔍 查询: 'AI'，过滤: category=ai")
    results = collection.query(
        query_texts=["AI"],
        n_results=2,
        where={"category": "ai"}
    )
    for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
        print(f"    {i+1}. {doc[:80]}... | meta={meta}")

    # 清理测试数据
    collection.delete(ids=ids)


def main():
    """主函数"""
    print("=" * 60)
    print("  Day 16: ChromaDB 向量数据库")
    print("=" * 60)

    try:
        collection = demo_chromadb_basics()
        demo_similarity_search(collection)
        demo_metadata_filter(collection)

        # 清理
        print(f"\n  🧹 清理 Collection")
        client = chromadb.PersistentClient(path=str(Path(__file__).parent / "chroma_db"))
        client.delete_collection("demo_collection")

        print("\n✅ ChromaDB 演示完成！")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
