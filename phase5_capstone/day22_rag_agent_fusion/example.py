"""
example.py — Day 22 完整演示：RAG + Agent 融合系统

演示内容：
1. 路由分类 — QueryRouter 对不同类型的查询分类
2. 缓存机制 — RAGAgentCache 的 TTL + LRU 行为
3. RAG 检索 — Agent 调用知识库检索工具
4. 多轮对话 — Agent 维护对话上下文
5. 完整 Agent 运行 — 多种路径（rag/direct/tool）对比
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent import ConversationalRAGAgent
from router import QueryRouter
from cache import RAGAgentCache
from retriever import RAGRetriever
from models import RAGResult


def demo_router():
    """演示 1：查询路由分类"""
    print("\n" + "=" * 60)
    print("  演示 1：查询路由 — 智能分类用户意图")
    print("=" * 60)

    router = QueryRouter()

    test_queries = [
        "什么是 RAG 检索增强生成？",
        "你好，今天天气真不错！",
        "帮我算一下 (123 + 456) * 7.5",
        "ChromaDB 和 Milvus 有什么区别？",
    ]

    try:
        for query in test_queries:
            result = router.classify(query)
            emoji = {"rag": "📚", "direct": "💬", "tool": "🔧"}.get(result["route"], "❓")
            print(f"\n  {emoji} [{result['route']}] {query}")
            print(f"     理由: {result['reason']}")
            print(f"     置信度: {result['confidence']:.0%}")
    except Exception as e:
        print(f"  ⚠️ LLM 调用失败: {e}")


def demo_cache():
    """演示 2：缓存机制"""
    print("\n" + "=" * 60)
    print("  演示 2：RAG 缓存 — TTL + LRU 双层策略")
    print("=" * 60)

    cache = RAGAgentCache(max_size=5, ttl_seconds=300)

    # 模拟检索结果
    mock_results = [
        RAGResult(content="测试文档内容 A", source="test_a.md", score=0.95),
        RAGResult(content="测试文档内容 B", source="test_b.md", score=0.82),
    ]

    # 第一次查询 — 缓存未命中
    print("\n  📝 第一次查询 '什么是 RAG'")
    result1 = cache.get("什么是 RAG")
    print(f"    命中: {result1 is not None}")

    # 存入缓存
    cache.set("什么是 RAG", mock_results)
    print(f"    已缓存, 当前大小: {cache.stats['size']}")

    # 第二次查询 — 缓存命中
    print("\n  📝 第二次查询 '什么是 RAG'")
    result2 = cache.get("什么是 RAG")
    print(f"    命中: {result2 is not None}")
    print(f"    结果数: {len(result2) if result2 else 0}")

    # 第三次查询 — 不同查询未命中
    print("\n  📝 第三次查询 'ChromaDB 怎么用'")
    result3 = cache.get("ChromaDB 怎么用")
    print(f"    命中: {result3 is not None}")

    print(f"\n  📊 缓存统计: {cache.stats}")


def demo_retriever():
    """演示 3：RAG 检索器 — 混合检索"""
    print("\n" + "=" * 60)
    print("  演示 3：RAG 检索器 — 为 Agent 提供知识检索")
    print("=" * 60)

    retriever = RAGRetriever()
    retriever.index()  # 构建索引

    test_queries = [
        "什么是 RAG？",
        "向量数据库是什么？",
        "Agent 和 MCP 的关系",
    ]

    for query in test_queries:
        print(f"\n  🔍 查询: {query}")
        results = retriever.search(query, top_k=2)
        for i, result in enumerate(results, 1):
            print(f"    [{i}] (来源:{result.source}, 分数:{result.score})")
            print(f"       {result.content[:80]}...")

    # 格式化输出（Agent 看到的上下文）
    print(f"\n  📋 Agent 收到的格式化文本:")
    formatted = retriever.format_for_llm(results)
    print(f"  {formatted[:200]}...")


def demo_rag_agent_direct():
    """演示 4：Agent 直接对话（不需要检索）"""
    print("\n" + "=" * 60)
    print("  演示 4：Agent 直接对话 — 闲聊/常识路由")
    print("=" * 60)

    agent = ConversationalRAGAgent()
    agent.verbose = True

    try:
        response = agent.run("你好！请介绍一下你自己，你能帮我做什么？")
        print(f"\n  ✅ 最终回答: {response.answer}")
        print(f"  📊 步数: {response.total_steps}, 耗时: {response.total_time_ms:.0f}ms")
    except Exception as e:
        print(f"  ⚠️ LLM 调用失败: {e}")


def demo_rag_agent_search():
    """演示 5：Agent RAG 检索 — 调用知识库工具"""
    print("\n" + "=" * 60)
    print("  演示 5：Agent RAG 检索 — 调用知识库获取答案")
    print("=" * 60)

    agent = ConversationalRAGAgent()
    agent.verbose = True

    try:
        response = agent.run("什么是 RAG？它为什么能减少 LLM 幻觉？")
        print(f"\n  ✅ 最终回答: {response.answer}")
        print(f"  📊 步数: {response.total_steps}, 耗时: {response.total_time_ms:.0f}ms")
        if response.sources:
            print(f"  📚 引用来源: {len(response.sources)} 条")
    except Exception as e:
        print(f"  ⚠️ LLM 调用失败: {e}")


def demo_multi_turn():
    """演示 6：多轮对话 — 上下文维护"""
    print("\n" + "=" * 60)
    print("  演示 6：多轮对话 — Agent 维护对话上下文")
    print("=" * 60)

    agent = ConversationalRAGAgent()
    agent.verbose = False  # 减少输出

    conversation = [
        "什么是向量数据库？",
        "它和传统数据库有什么区别？",  # "它"指代向量数据库
        "那 ChromaDB 属于哪一种？",
    ]

    try:
        for i, query in enumerate(conversation, 1):
            print(f"\n  👤 用户[{i}]: {query}")
            response = agent.run(query)
            answer_preview = response.answer[:120].replace("\n", " ")
            print(f"  🤖 Agent[{i}]: {answer_preview}...")
            print(f"     (步数:{response.total_steps}, 耗时:{response.total_time_ms:.0f}ms)")

        print(f"\n  📊 Agent 统计: {agent.stats}")
    except Exception as e:
        print(f"  ⚠️ LLM 调用失败: {e}")


def main():
    """主函数 — 运行所有演示"""
    print("=" * 60)
    print("  Day 22: RAG + Agent 融合系统")
    print("  Agent 调度 RAG | 路由分类 | 缓存 | 多轮对话")
    print("=" * 60)

    try:
        # 先运行不需要 Agent 的演示（缓存和检索器可独立运行）
        demo_cache()
        demo_retriever()

        # 路由演示（需要 LLM）
        demo_router()

        # Agent 演示（需要 LLM）
        demo_rag_agent_direct()
        demo_rag_agent_search()
        demo_multi_turn()

        print("\n" + "=" * 60)
        print("  ✅ Day 22 所有演示完成！")
        print("=" * 60)
        print("\n  💡 Day 22 关键要点：")
        print("    1. RAG + Agent 融合 = Agent 调度 RAG（非固定管道）")
        print("    2. QueryRouter — LLM 驱动的意图分类")
        print("    3. RAGAgentCache — TTL + LRU 双层缓存")
        print("    4. RAGRetriever — 混合检索（BM25 + 向量 + RRF）")
        print("    5. ConversationalRAGAgent — ReAct 循环 + 工具调用")
        print("    6. 多轮对话 — 上下文维护 + 引用追踪")

    except Exception as e:
        print(f"\n  ❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
