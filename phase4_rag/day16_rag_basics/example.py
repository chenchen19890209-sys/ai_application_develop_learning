"""
example.py — Day 16 完整演示：RAG 原理与向量数据库

演示内容：
1. 嵌入模型 — 语义相似度直观感受
2. ChromaDB — 向量数据库增删查操作
3. RAG — 检索增强生成的完整流程
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import embedding_demo
import chromadb_demo
import rag_basics


def main():
    """主函数"""
    print("=" * 60)
    print("  Day 16: RAG 原理与向量数据库")
    print("  嵌入模型 | ChromaDB | RAG 三段式")
    print("=" * 60)

    try:
        # 演示 1：嵌入模型
        print("\n" + "─" * 50)
        print("  阶段 1/3: 文本嵌入")
        print("─" * 50)
        embedding_demo.main()

        # 演示 2：ChromaDB
        print("\n" + "─" * 50)
        print("  阶段 2/3: 向量数据库")
        print("─" * 50)
        chromadb_demo.main()

        # 演示 3：RAG
        print("\n" + "─" * 50)
        print("  阶段 3/3: RAG 系统")
        print("─" * 50)
        rag_basics.main()

        print("\n" + "=" * 60)
        print("  ✅ Day 16 所有演示完成！")
        print("=" * 60)
        print("\n  💡 Day 16 关键要点：")
        print("    1. 嵌入 — 将文本语义映射到向量空间，相似文本距离近")
        print("    2. ChromaDB — 向量数据库实现高效的相似度搜索")
        print("    3. RAG — 索引(存入) → 检索(Top-K) → 生成(LLM) 三段式")
        print("    4. RAG 的核心优势：基于外部知识回答问题，减少幻觉")
    except Exception as e:
        print(f"\n  ❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
