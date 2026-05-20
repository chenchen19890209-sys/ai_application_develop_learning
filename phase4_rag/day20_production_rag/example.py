"""
example.py — Day 20 完整演示：生产级 RAG 系统

演示内容：
1. 基础查询 — 完整管道：缓存→检索→重排→生成
2. 缓存命中 — 重复查询零 API 成本
3. 混合检索 — BM25 + Vector + RRF 融合对比
4. 健康检查 — 一键诊断所有组件
5. 性能指标 — 延迟分布、命中率、错误统计
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import time
from rag_config import RAGConfig
from production_rag import ProductionRAG


def demo_basic_query():
    """演示 1：基础生产级查询"""
    print("\n" + "=" * 60)
    print("  演示 1：基础生产级查询")
    print("=" * 60)

    config = RAGConfig(use_hybrid=False, use_reranker=False)
    rag = ProductionRAG(config)

    # 索引示例文档
    docs = [
        "Python 是一种解释型、面向对象的高级编程语言，由 Guido van Rossum 于 1991 年创建。"
        "Python 的设计哲学强调代码的可读性和简洁性。",

        "机器学习是人工智能的一个分支，使计算机能从数据中学习而无需明确编程。"
        "主要方法包括监督学习、无监督学习和强化学习。",

        "RAG（检索增强生成）结合了信息检索和文本生成。它先从知识库检索相关文档，"
        "再将文档作为上下文提供给 LLM 生成更准确的答案。",

        "深度学习使用多层神经网络学习数据的层次化表示。CNN 擅长图像识别，"
        "RNN 适合序列数据，Transformer 架构改变了 NLP 领域。",

        "ChromaDB 是开源向量数据库，专为 AI 应用的语义搜索设计。"
        "它支持嵌入存储、近似最近邻检索，可轻松集成到 RAG 系统。",
    ]
    rag.index_documents(docs)

    queries = [
        "Python 是什么时候创建的？",
        "什么是机器学习？",
        "RAG 如何减少幻觉？",
    ]

    for q in queries:
        print(f"\n  👤 查询: {q}")
        try:
            result = rag.query(q)
            print(f"  ✅ 回答: {result['answer'][:200]}...")
            print(f"  ⏱ 耗时: {result['timing']['total_ms']:.0f}ms")
            print(f"  📦 缓存: {result['cached']}")
            if result['sources']:
                print(f"  📚 来源数: {len(result['sources'])}")
        except Exception as e:
            print(f"  ⚠️ 查询失败: {e}")

    rag.reset()


def demo_cache():
    """演示 2：缓存命中对比"""
    print("\n" + "=" * 60)
    print("  演示 2：缓存命中 — 零 API 成本")
    print("=" * 60)

    rag = ProductionRAG(RAGConfig(use_hybrid=False, use_reranker=False))
    rag.index_documents(["Python 由 Guido van Rossum 于 1991 年创建。"])

    query = "Python 是谁创建的？"

    print(f"\n  🔄 第 1 次查询（完整管道）...")
    r1 = rag.query(query)
    print(f"  📦 缓存: {r1['cached']}, 耗时: {r1['timing']['total_ms']:.0f}ms")

    print(f"\n  🔄 第 2 次查询（应命中缓存）...")
    r2 = rag.query(query)
    print(f"  📦 缓存: {r2['cached']}, 耗时: {r2['timing']['total_ms']:.0f}ms")

    speedup = r1['timing']['total_ms'] / max(r2['timing']['total_ms'], 0.1)
    print(f"\n  💡 缓存加速约 {speedup:.0f}x，且第 2 次查询零 API 调用成本！")

    print(f"\n  📊 缓存统计: {rag.get_stats()}")
    rag.reset()


def demo_hybrid():
    """演示 3：混合检索效果演示"""
    print("\n" + "=" * 60)
    print("  演示 3：混合检索 — BM25 + Vector + RRF")
    print("=" * 60)

    # 开启混合检索
    rag = ProductionRAG(RAGConfig(use_hybrid=True, use_reranker=False, top_k=3))

    docs = [
        "Python 是一种广泛用于数据科学和机器学习的编程语言。",
        "机器学习是人工智能的一个分支，使用 Python 作为主要语言。",
        "Java 是一种面向对象的编程语言，广泛用于企业级应用开发。",
        "深度学习使用神经网络进行模式识别和预测分析。",
        "RAG 技术通过检索知识库来增强大语言模型的生成质量。",
        "向量数据库存储嵌入向量用于高效的语义相似度搜索。",
    ]
    rag.index_documents(docs)

    print(f"\n  🔍 查询: 'Python 在机器学习中的应用'")
    result = rag.query("Python 在机器学习中的应用")
    print(f"  ✅ 回答: {result['answer'][:200]}...")
    print(f"\n  📚 检索来源:")
    for i, source in enumerate(result.get('sources', []), 1):
        print(f"    {i}. (分数:{source['score']:.4f}) {source['content'][:80]}...")

    rag.reset()


def demo_health():
    """演示 4：健康检查和指标"""
    print("\n" + "=" * 60)
    print("  演示 4：健康检查 + 性能指标")
    print("=" * 60)

    rag = ProductionRAG(RAGConfig(use_hybrid=False, use_reranker=False))
    rag.index_documents(["测试文档：用于健康检查和指标验证。"])

    # 执行几次查询生成指标数据
    for q in ["测试文档说什么？", "测试文档说什么？", "有什么内容？"]:
        try:
            rag.query(q)
        except Exception:
            pass

    print(f"\n  🏥 健康检查:")
    health = rag.health_check()
    for k, v in health.items():
        if isinstance(v, dict):
            status = v.get("status", v)
            print(f"    {k}: {status}")
        else:
            print(f"    {k}: {v}")

    print(f"\n  📊 性能指标:")
    stats = rag.get_stats()
    for k, v in stats.items():
        if isinstance(v, float):
            print(f"    {k}: {v:.4f}" if v < 1 else f"    {k}: {v:.1f}")
        else:
            print(f"    {k}: {v}")

    rag.reset()


def demo_full_pipeline():
    """演示 5：完整生产管道（混合检索 + 重排序）"""
    print("\n" + "=" * 60)
    print("  演示 5：完整生产管道（混合检索 + 重排序）")
    print("=" * 60)

    try:
        rag = ProductionRAG(RAGConfig(use_hybrid=True, use_reranker=True, top_k=3))
    except Exception as e:
        print(f"  ⚠️ 重排序模型加载失败（可能内存不足）: {e}")
        print(f"  💡 降级为混合检索模式")
        rag = ProductionRAG(RAGConfig(use_hybrid=True, use_reranker=False, top_k=3))

    docs = [
        "Transformer 架构由 Vaswani 等人在 2017 年提出，基于自注意力机制。"
        "它解决了 RNN 无法并行计算的问题，成为现代 LLM 的基础架构。",

        "GPT 系列模型基于 Transformer 的 Decoder 部分，通过大规模预训练展现强大的文本生成能力。",

        "BERT 基于 Transformer 的 Encoder 部分，通过掩码语言模型预训练，在理解任务上表现出色。",

        "自注意力机制允许模型在处理每个词时关注输入序列中的所有词，从而捕捉长距离依赖关系。",

        "残差连接和层归一化是 Transformer 架构的重要组成部分，帮助训练深层网络。",
    ]
    rag.index_documents(docs)

    query = "Transformer 架构的核心创新是什么？"
    print(f"\n  🔍 查询: '{query}'")
    result = rag.query(query)
    print(f"  ✅ 回答: {result['answer'][:300]}...")
    print(f"  ⏱ 总耗时: {result['timing']['total_ms']:.0f}ms")
    print(f"    检索: {result['timing']['retrieval_ms']:.0f}ms")
    print(f"    重排: {result['timing']['rerank_ms']:.0f}ms")
    print(f"    生成: {result['timing']['generation_ms']:.0f}ms")

    rag.reset()


def main():
    """主函数 — 运行所有演示"""
    print("=" * 60)
    print("  Day 20: 生产级 RAG 系统")
    print("  配置 | 日志 | 缓存 | 重试 | 混合检索 | 重排序 | 指标")
    print("=" * 60)
    print("  零 LangChain 依赖 — 原生 ChromaDB + openai SDK")
    print("=" * 60)

    try:
        demo_basic_query()
        demo_cache()
        demo_hybrid()
        demo_health()
        demo_full_pipeline()

        print("\n" + "=" * 60)
        print("  ✅ Day 20 所有演示完成！")
        print("=" * 60)
        print("\n  💡 Day 20 关键要点：")
        print("    1. ProductionRAG = 完整管道（缓存→检索→重排→生成→指标）")
        print("    2. RAGConfig 集中管理所有参数，支持环境变量覆盖")
        print("    3. StructuredLogger — JSON 格式日志，ELK/Splunk 可采集")
        print("    4. TTLCache — TTL 过期 + LRU 淘汰，减少重复查询成本")
        print("    5. 指数退避重试 — 应对 API 瞬时故障")
        print("    6. 混合检索（BM25+Vector+RRF）+ 重排序 是工业标准")
        print("    7. health_check() — 一键诊断所有组件状态")
        print("    8. MetricsTracker — P50/P95 延迟、命中率、错误率")
        print("\n  🎉 Phase 4（RAG 实战）完成！")

    except Exception as e:
        print(f"\n  ❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()
        print("\n  💡 提示：请检查 .env 文件中 OPENAI_API_KEY 配置")


if __name__ == "__main__":
    main()
