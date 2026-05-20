"""
embedding_demo.py — 文本嵌入与向量操作

功能：
1. 加载中文嵌入模型（BAAI/bge-small-zh-v1.5）
2. 文本转向量（embedding）
3. 计算向量相似度（余弦相似度）
4. 演示嵌入的语义理解能力

设计原则：
- 使用 HF_ENDPOINT 镜像加速模型下载
- 零 LangChain 依赖
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import HF_ENDPOINT

import os
# 设置 HuggingFace 镜像（必须在导入 sentence_transformers 之前）
os.environ["HF_ENDPOINT"] = HF_ENDPOINT if HF_ENDPOINT else "https://hf-mirror.com"

import numpy as np
from sentence_transformers import SentenceTransformer


def cos_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """计算两个向量的余弦相似度 — 范围 [-1, 1]，越大越相似"""
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))


def demo_embedding_basics():
    """演示 1：基础嵌入 — 文本转语义向量"""
    print("=" * 60)
    print("  嵌入基础 — 文本转语义向量")
    print("=" * 60)

    # 加载模型（首次运行会自动下载）
    model_name = "BAAI/bge-small-zh-v1.5"
    print(f"\n  📦 加载模型: {model_name}")
    model = SentenceTransformer(model_name)

    # 单文本嵌入
    text = "Python 是一种流行的编程语言"
    embedding = model.encode(text)
    print(f"  输入: '{text}'")
    print(f"  向量维度: {embedding.shape[0]}")
    print(f"  向量前10维: {embedding[:10].round(4)}")

    return model


def demo_similarity(model):
    """演示 2：语义相似度 — 嵌入反映语义关系"""
    print("\n" + "=" * 60)
    print("  语义相似度计算")
    print("=" * 60)

    # 三组文本：同义、相关、无关
    query = "人工智能的发展"
    candidates = [
        "AI 技术的进步",
        "机器学习是 AI 的一个分支",
        "今天天气很好适合出去玩",
    ]

    query_emb = model.encode(query)
    print(f"\n  查询: '{query}'")
    print(f"  {'─'*40}")

    for candidate in candidates:
        cand_emb = model.encode(candidate)
        sim = cos_similarity(query_emb, cand_emb)
        bar = "█" * int(sim * 20)
        print(f"  '{candidate}'")
        print(f"  相似度: {sim:.4f} {bar}")
        print()

    return model


def demo_batch_embedding(model):
    """演示 3：批量嵌入 — 高效处理多文本"""
    print("=" * 60)
    print("  批量嵌入")
    print("=" * 60)

    documents = [
        "Python 是一种解释型编程语言",
        "JavaScript 主要用于 Web 前端开发",
        "深度学习使用神经网络进行特征学习",
        "数据库用于存储和查询结构化数据",
    ]

    embeddings = model.encode(documents, show_progress_bar=True)
    print(f"\n  共处理 {len(documents)} 篇文档")
    print(f"  嵌入矩阵形状: {embeddings.shape}")

    # 计算文档间的相似度矩阵
    print(f"\n  文档相似度矩阵:")
    for i in range(len(documents)):
        for j in range(i + 1, len(documents)):
            sim = cos_similarity(embeddings[i], embeddings[j])
            print(f"    Doc{i} vs Doc{j}: {sim:.4f}")


def main():
    """主函数"""
    print("=" * 60)
    print("  Day 16: 文本嵌入与向量操作")
    print("=" * 60)

    try:
        model = demo_embedding_basics()
        demo_similarity(model)
        demo_batch_embedding(model)
        print("\n✅ 嵌入演示完成！")
        print("💡 关键理解：嵌入将语义相近的文本映射到相邻的向量空间")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        print("💡 确保已安装 sentence-transformers 且网络可访问 HF 镜像")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
