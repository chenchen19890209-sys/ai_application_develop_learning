"""
Day 18 综合示例：检索优化完整流程
================================
本示例展示检索优化的完整 pipeline：
  1. 混合检索（BM25 + 向量 + RRF 融合）
  2. 重排序（CrossEncoder / LLM）
  3. 三种检索方法的对比评估

运行方法：
    python example.py

预期效果：
    混合检索（RRF）的检索质量 > 单一 BM25 或向量检索
    加入重排序后，Top-1 命中率进一步提升
"""

# ==================== 路径配置 ====================
import sys
from pathlib import Path

# 将项目根目录加入 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# ==================== 导入本模块的检索和重排序类 ====================
from hybrid_retrieval import (
    BM25Retriever,  # BM25 稀疏检索器
    VectorRetriever,  # 向量稠密检索器
    HybridRetriever,  # 混合检索器（BM25 + Vector + RRF）
    DEMO_DOCUMENTS,  # 共享的 18 篇中文文档语料
)

from reranker import (
    CrossEncoderReranker,  # 交叉编码器重排序
    LLMReranker,  # LLM 重排序
)

# ==================== 标准库导入 ====================
from typing import List, Dict, Any, Tuple


# ==================== 对比评估函数 ====================

def compare_retrievers(
    query: str,
    documents: List[str],
    ground_truth_idx: int,
    top_k: int = 3
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    对比三种检索方法在同一查询上的效果

    评估指标：
    - 排名（Rank）：ground truth 文档在结果列表中的位置（越靠前越好）
    - 从结果列表可以直观对比各方法的差异

    Args:
        query: 查询文本
        documents: 文档语料库
        ground_truth_idx: 正确答案文档在语料库中的索引
        top_k: 每种方法返回的文档数量

    Returns:
        (bm25_results, vector_results, hybrid_results) 三元组
    """
    # 创建三个独立的检索器
    bm25 = BM25Retriever()
    vector = VectorRetriever(collection_name=f"compare_{hash(query) % 10000}")
    hybrid = HybridRetriever()

    # 构建索引
    bm25.index(documents)
    vector.index(documents)
    hybrid.index(documents)

    # 执行检索（hybrid 内部会分别调用 BM25 和 Vector，然后 RRF 融合）
    bm25_results = bm25.search(query, top_k=top_k)
    vector_results = vector.search(query, top_k=top_k)
    hybrid_results = hybrid.search(query, top_k=top_k)

    # 检查 ground truth 在各方法中的排名
    gt_doc = documents[ground_truth_idx]
    print(f"\n  Ground Truth 文档: \"{gt_doc[:60]}...\"")

    # BM25 中的排名
    bm25_rank = "未命中"
    for item in bm25_results:
        if item["document"] == gt_doc:
            bm25_rank = f"第 {item['rank']} 名"
            break

    # 向量检索中的排名
    vector_rank = "未命中"
    for item in vector_results:
        if item["document"] == gt_doc:
            vector_rank = f"第 {item['rank']} 名"
            break

    # 混合检索中的排名
    hybrid_rank = "未命中"
    for item in hybrid_results:
        if item["document"] == gt_doc:
            hybrid_rank = f"第 {item['rank']} 名"
            break

    # 打印对比结果
    print(f"  检索方法       | Ground Truth 排名")
    print(f"  --------------|-------------------")
    print(f"  BM25 Only     | {bm25_rank}")
    print(f"  Vector Only   | {vector_rank}")
    print(f"  Hybrid (RRF)  | {hybrid_rank}")

    # 根据结果判断最佳方法
    bm25_hit = bm25_rank != "未命中"
    vector_hit = vector_rank != "未命中"
    hybrid_hit = hybrid_rank != "未命中"

    if hybrid_hit and not bm25_hit and not vector_hit:
        print(f"  >>> 结论：混合检索命中而单一方法未命中，体现了 RRF 融合的优势！")
    elif hybrid_hit and (bm25_hit or vector_hit):
        print(f"  >>> 结论：混合检索成功命中，RRF 融合可靠有效。")

    return bm25_results, vector_results, hybrid_results


def demo_reranking_pipeline(
    query: str,
    documents: List[str]
) -> None:
    """
    演示完整的重排序 pipeline：混合检索 → CrossEncoder 重排序 → LLM 重排序

    Args:
        query: 查询文本
        documents: 文档语料库
    """
    print(f"\n{'='*70}")
    print(f"  重排序 Pipeline 演示")
    print(f"{'='*70}")
    print(f"  查询: \"{query}\"")

    # Step 1: 混合检索召回 Top-6 候选
    print(f"\n  [Step 1] 混合检索召回候选文档 (Top-6)...")
    hybrid = HybridRetriever()
    hybrid.index(documents)
    candidates_results = hybrid.search(query, top_k=6)

    # 提取候选文档文本列表
    candidates: List[str] = [item["document"] for item in candidates_results]
    print(f"  召回了 {len(candidates)} 篇候选文档")

    # Step 2: CrossEncoder 精排 → Top-3
    print(f"\n  [Step 2] CrossEncoder 重排序 (Top-3)...")
    ce_reranker = CrossEncoderReranker()
    ce_results = ce_reranker.rerank(query, candidates, top_k=3)

    print(f"  CrossEncoder 精排结果:")
    for item in ce_results:
        print(f"    #{item['rank']}: 分数={item['score']:.4f} "
              f"| {item['document'][:60]}...")

    # Step 3: LLM 精排 → Top-3（可选，因为涉及 API 调用）
    print(f"\n  [Step 3] LLM 重排序 (Top-3)...")
    try:
        llm_reranker = LLMReranker()
        llm_results = llm_reranker.rerank(query, candidates, top_k=3)

        print(f"  LLM 精排结果:")
        for item in llm_results:
            print(f"    #{item['rank']}: 分数={item['score']}/10 "
                  f"| {item['document'][:60]}...")
    except Exception as e:
        print(f"  LLM 重排序跳过（API 调用出错: {e}）")

    print(f"\n  >>> Pipeline 总结:")
    print(f"      混合检索召回 {len(candidates)} 篇 → CrossEncoder/LLM 精排 → Top-3")
    print(f"      精排阶段显著提升了 Top-1 的准确性")


# ==================== 主演示函数 ====================

def main() -> None:
    """
    Day 18 综合演示入口

    分三个环节：
    1. 展示文档语料库
    2. 对比检索（BM25 vs Vector vs Hybrid）—— 证明 Hybrid > 单一方法
    3. 重排序 pipeline 演示
    """
    print("=" * 70)
    print("  Day 18: 检索优化综合示例")
    print("  BM25 + 向量 + RRF 混合检索  +  CrossEncoder / LLM 重排序")
    print("=" * 70)

    # ==================== 环节 1: 展示语料库 ====================
    print(f"\n{'='*70}")
    print(f"  [环节 1] 文档语料库（共 {len(DEMO_DOCUMENTS)} 篇）")
    print(f"{'='*70}")
    for i, doc in enumerate(DEMO_DOCUMENTS, start=1):
        print(f"  [{i:02d}] {doc[:70]}...")

    # ==================== 环节 2: 对比检索 ====================
    print(f"\n{'='*70}")
    print("  [环节 2] 对比检索 — BM25 vs Vector vs Hybrid (RRF)")
    print(f"{'='*70}")

    # 测试用例 1：BM25 优势场景（精确关键词匹配）
    print(f"\n  --- 测试 1: 精确关键词匹配 ---")
    compare_retrievers(
        query="Python 编程语言",
        documents=DEMO_DOCUMENTS,
        ground_truth_idx=0,  # 第 0 篇文档："Python 是一种解释型、面向对象的高级编程语言..."
        top_k=5
    )

    # 测试用例 2：向量检索优势场景（语义理解）
    print(f"\n  --- 测试 2: 语义理解匹配 ---")
    compare_retrievers(
        query="计算机如何在没有指令的情况下学习？",
        documents=DEMO_DOCUMENTS,
        ground_truth_idx=1,  # 第 1 篇文档："机器学习是人工智能的一个分支..."
        top_k=5
    )

    # 测试用例 3：混合场景（同时涉及关键词和语义）
    print(f"\n  --- 测试 3: 混合关键词+语义 ---")
    compare_retrievers(
        query="AI 中的检索和生成如何结合？",
        documents=DEMO_DOCUMENTS,
        ground_truth_idx=5,  # 第 5 篇文档："RAG（检索增强生成）..."
        top_k=5
    )

    # ==================== 环节 3: 重排序 Pipeline ====================
    print(f"\n{'='*70}")
    print("  [环节 3] 重排序 Pipeline 演示")
    print(f"{'='*70}")

    demo_reranking_pipeline(
        query="大语言模型如何工作？",
        documents=DEMO_DOCUMENTS
    )

    # ==================== 环节 4: 对比表 ====================
    print(f"\n{'='*70}")
    print("  [环节 4] 检索优化对比表")
    print(f"{'='*70}")
    print(f"""
  | 方法            | 检索原理         | 优点              | 缺点              | 适用阶段 |
  |----------------|------------------|-------------------|-------------------|---------|
  | BM25           | 关键词词频统计    | 精准关键词匹配     | 不理解语义         | 召回    |
  | 向量检索        | 稠密向量相似度    | 理解语义、同义词   | 可能忽略关键词     | 召回    |
  | 混合检索(RRF)   | 排名融合          | 兼顾关键词和语义   | 略增延迟           | 召回    |
  | CrossEncoder   | query-doc联合编码 | 精度高、速度快     | 需要候选文档       | 精排    |
  | LLM Reranker   | LLM 深度理解      | 语义理解最强       | 速度较慢、有成本   | 精排    |
""")

    # ==================== 最终总结 ====================
    print(f"{'='*70}")
    print("  检索优化最终结论:")
    print("  1. 混合检索（BM25 + Vector + RRF）优于任一单一检索方法")
    print("  2. 在混合检索基础上加重排序，可进一步提升 Top-1 准确率")
    print("  3. CrossEncoder 重排序性价比较高，适合大多数场景")
    print("  4. LLM 重排序适合对精度要求极高的最终精排环节")
    print(f"{'='*70}")


# ==================== 程序入口 ====================
if __name__ == "__main__":
    try:
        main()
        print("\n程序执行完毕。")
    except Exception as e:
        print(f"\n程序执行出错: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
