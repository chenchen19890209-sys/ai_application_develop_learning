"""
Day19 完整示例: RAG 评估与会话式 RAG

本示例演示:
1. 使用 RAGEvaluator 评估 RAG 回答质量（忠实度、相关性、完整性）
2. 使用 RetrievalEvaluator 评估检索质量（Precision, Recall, NDCG）
3. 使用 ConversationRAG 进行多轮知识对话

运行方式:
    python example.py
"""

import sys
from pathlib import Path

# ==================== 导入本日模块 ====================
sys.path.insert(0, str(Path(__file__).parent))  # 将当前目录加入 sys.path，以便 import 同目录下的模块
from rag_evaluation import RAGEvaluator, RetrievalEvaluator, cosine_similarity  # RAG 评估相关
from conversation_rag import ConversationRAG, build_knowledge_base             # 对话式 RAG 相关


def demo_retrieval_evaluation() -> None:
    """
    演示 1: 检索质量评估

    用模拟的检索结果展示 Precision@K、Recall@K、NDCG@K 和 MRR 的计算
    """
    print("=" * 60)
    print(" 演示 1: 检索质量评估（RetrievalEvaluator）")
    print("=" * 60)

    evaluator: RetrievalEvaluator = RetrievalEvaluator()  # 实例化检索评估器

    # 模拟数据: 一个查询的检索结果和标注的相关文档
    # 检索系统返回的文档 ID（按相关性从高到低排序）
    retrieved: list[str] = [
        "doc_C", "doc_A", "doc_E", "doc_B", "doc_D",
        "doc_F", "doc_G", "doc_H", "doc_I", "doc_J",
    ]
    # 人工标注的相关文档 ID（ground truth）
    relevant: list[str] = ["doc_A", "doc_B", "doc_C", "doc_D"]

    print(f"检索结果 (Top-10): {retrieved}")
    print(f"相关文档: {relevant}")
    print()

    # 计算各指标并打印
    results = evaluator.evaluate_all(retrieved, relevant, k_values=[1, 3, 5, 10])
    for metric, value in results.items():
        print(f"  {metric}: {value}")

    # 计算 MRR（单个查询的 Reciprocal Rank）
    mrr: float = evaluator.mrr(
        {"q1": relevant},   # 查询-相关文档映射
        {"q1": retrieved},  # 查询-检索结果映射
    )
    print(f"  MRR: {mrr}")

    # 解读 P@K 和 R@K
    print("\n解读:")
    print("  P@5 = 4/5 = 0.8 说明: 前 5 个结果中 80% 是相关的")
    print("  R@5 = 4/4 = 1.0 说明: 前 5 个结果覆盖了 100% 的相关文档")
    print("  NDCG@5 考虑了排名位置，相关文档越靠前得分越高")
    print()


def demo_rag_answer_evaluation() -> None:
    """
    演示 2: RAG 回答质量评估

    模拟一次完整的 RAG 流程（查询 -> 检索 -> 生成），然后用 RAGEvaluator 评估结果
    """
    print("=" * 60)
    print(" 演示 2: RAG 回答质量评估（RAGEvaluator）")
    print("=" * 60)

    evaluator: RAGEvaluator = RAGEvaluator()  # 实例化

    # ---- 模拟一个 RAG 系统的查询和检索结果 ----
    query: str = "Python 的设计哲学是什么？"

    # 检索返回的文档（模拟）
    context_docs: list[str] = [
        "Python 是一种解释型、面向对象的高级编程语言，由 Guido van Rossum 于 1991 年发布。"
        "Python 的设计哲学强调代码的可读性和简洁性，",
        "Python 采用动态类型系统和垃圾回收机制，支持多种编程范式，包括面向对象、"
        "函数式编程和过程式编程。Python 的核心哲学之一是 '做一件事应该只有一种最好的方法'。",
    ]

    # RAG 系统生成的回答（模拟）
    answer: str = (
        "Python 的设计哲学强调代码的可读性和简洁性。"
        "它由 Guido van Rossum 于 1991 年发布，"
        "并且核心哲学是 '做一件事应该只有一种最好的方法'。"
    )

    # ---- 执行一站式评估 ----
    print(f"\n查询: {query}")
    print(f"回答: {answer}")
    print(f"检索文档数: {len(context_docs)} 篇")

    result = evaluator.evaluate_all(query, answer, context_docs)  # 一站式评估

    # ---- 打印评估结果 ----
    print("\n--- 评估结果 ---")
    summary = result["summary"]
    print(f"  忠实度 (Faithfulness):  {summary['faithfulness_score']:.2%}")
    print(f"    回答是否完全基于文档？有无幻觉？")
    print(f"  相关性 (Relevance):     {summary['relevance_score']:.2%}")
    print(f"    检索的文档与查询相关吗？")
    print(f"  完整性 (Completeness):  {summary['completeness_score']:.2%}")
    print(f"    回答是否覆盖了文档的关键信息？")
    print(f"  -----------------------------------")
    print(f"  综合得分:               {summary['overall_score']:.2%}")

    # 打印忠实度详情
    faith = result["faithfulness"]
    print(f"\n忠实度详情: {faith['score']}")
    print(f"  有支撑的声明: {len(faith['supported_claims'])} 条")
    print(f"  无支撑的声明: {len(faith['unsupported_claims'])} 条")

    # 打印相关性详情
    rel = result["relevance"]
    print(f"\n文档相关性详情: 均值={rel['mean_score']}")
    for i, s in enumerate(rel["per_doc_scores"], 1):
        print(f"  文档 {i}: 相似度={s}")

    # 打印完整性详情
    comp = result["completeness"]
    print(f"\n完整性详情: {comp['score']}")
    print(f"  覆盖的信息点: {len(comp['covered_points'])} 个")
    print(f"  遗漏的信息点: {len(comp['missed_points'])} 个")
    print()


def demo_conversation_rag() -> None:
    """
    演示 3: 对话式 RAG — 多轮知识对话

    构建一个小型编程知识库，然后进行多轮对话
    """
    print("=" * 60)
    print(" 演示 3: 对话式 RAG（ConversationRAG）")
    print("=" * 60)

    # ---- 第 1 步: 构建知识库 ----
    knowledge_docs: list[str] = [
        # 几篇关于编程语言的短文档
        "Python 由 Guido van Rossum 创建于 1991 年，设计哲学强调可读性和简洁。"
        "它支持面向对象、函数式和过程式编程范式。",
        "RAG 技术（检索增强生成）结合了信息检索和文本生成。"
        "它先从外部知识库中检索相关文档，再让 LLM 基于这些文档生成更准确的回答，"
        "从而减少幻觉。",
        "ChromaDB 是一个开源的向量数据库，用于 AI 应用的语义搜索。"
        "它原生支持嵌入存储、近似最近邻检索，可以轻松集成到 RAG 系统中。",
        "向量数据库通过把文本转换为高维向量来实现语义搜索。"
        "相似的文本在向量空间中距离更近，因此可以找到语义相关而非仅仅关键词匹配的结果。",
        "LangChain 是一个用于构建 LLM 应用的开源框架，版本 0.2.x 仍是稳定版本。"
        "它提供了链式调用、Agent、RAG 等模块，帮助开发者快速构建复杂应用。",
    ]

    kb = build_knowledge_base(knowledge_docs)  # 构建 ChromaDB 知识库
    rag = ConversationRAG(knowledge_base=kb)   # 创建对话式 RAG 实例

    # ---- 第 2 步: 多轮对话测试 ----
    print("\n模拟多轮对话:\n")

    # 第 1 轮: 简单寒暄（应跳过检索）
    print("-" * 40)
    print("用户: 你好，我想了解一些编程知识。")
    response1: str = rag.chat("你好，我想了解一些编程知识。")
    print(f"助手: {response1[:200]}")
    print()

    # 第 2 轮: 知识查询（应触发检索）
    print("-" * 40)
    print("用户: Python 是谁创建的？")
    response2: str = rag.chat("Python 是谁创建的？")
    print(f"助手: {response2[:200]}")
    print()

    # 第 3 轮: 上下文相关追问（应查询重写后检索）
    print("-" * 40)
    print("用户: 它的设计哲学是什么？")
    response3: str = rag.chat("它的设计哲学是什么？")
    print(f"助手: {response3[:200]}")
    print()

    # 第 4 轮: RAG 相关话题
    print("-" * 40)
    print("用户: RAG 是如何减少幻觉的？")
    response4: str = rag.chat("RAG 是如何减少幻觉的？")
    print(f"助手: {response4[:200]}")
    print()

    # 第 5 轮: 上下文追问
    print("-" * 40)
    print("用户: 那 ChromaDB 在 RAG 系统中起什么作用？")
    response5: str = rag.chat("那 ChromaDB 在 RAG 系统中起什么作用？")
    print(f"助手: {response5[:200]}")

    # ---- 展示完整对话历史 ----
    print("\n" + "=" * 40)
    print(" 完整对话历史:")
    print("=" * 40)
    history = rag.get_history()
    for i, msg in enumerate(history, 1):
        role_label: str = "用户" if msg["role"] == "user" else "助手"
        content_short: str = msg["content"][:100]
        print(f"  [{i}] {role_label}: {content_short}{'...' if len(msg['content']) > 100 else ''}")

    # 清理会话
    rag.clear_session("default")
    print("\n会话已清理。")


def main() -> None:
    """
    主函数: 依次运行三个演示

    使用 try/except 包裹，确保异常信息友好展示
    """
    print("\n" + "=" * 60)
    print("  Day19: RAG 评估与对话式 RAG — 完整示例")
    print("=" * 60)
    print()

    try:
        # ---- 演示 1: 检索评估（无需 API，可独立运行） ----
        demo_retrieval_evaluation()

        # ---- 演示 2: 回答质量评估（需要 LLM API） ----
        demo_rag_answer_evaluation()

        # ---- 演示 3: 对话式 RAG（需要 LLM API + ChromaDB） ----
        demo_conversation_rag()

        print("=" * 60)
        print(" 所有演示完成！")
        print("=" * 60)

    except Exception as e:
        # 捕获并友好展示错误信息
        print(f"\n运行出错: {type(e).__name__}: {e}")
        print("\n请检查:")
        print("  1. .env 文件中是否正确配置了 OPENAI_API_KEY")
        print("  2. 网络连接是否正常")
        print("  3. 依赖包是否已安装: pip install -r requirements.txt")


# ==================== 入口点 ====================
if __name__ == "__main__":
    main()  # 用 try/except 包裹了异常处理
