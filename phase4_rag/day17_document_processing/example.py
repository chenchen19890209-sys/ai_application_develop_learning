"""
example.py — Day 17 完整演示：文档处理与基础 RAG

演示内容：
1. 文档加载 — 多格式文本加载
2. 分块策略 — 固定大小 / 句子边界 / 滑动窗口
3. 构建 RAG — 文档索引 + 检索 + 生成
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import document_loader
import build_rag


def main():
    """主函数"""
    print("=" * 60)
    print("  Day 17: 文档处理与基础 RAG")
    print("  文档加载 | 分块策略 | RAG 构建")
    print("=" * 60)

    try:
        # 演示 1：文档加载和分块
        print("\n" + "─" * 50)
        print("  阶段 1/2: 文档处理")
        print("─" * 50)
        document_loader.demo_loading()

        # 演示 2：构建 RAG
        print("\n" + "─" * 50)
        print("  阶段 2/2: 构建 RAG 系统")
        print("─" * 50)
        build_rag.main()

        print("\n" + "=" * 60)
        print("  ✅ Day 17 所有演示完成！")
        print("=" * 60)
        print("\n  💡 Day 17 关键要点：")
        print("    1. 文档加载 — 支持 TXT/MD/PY 等多种格式")
        print("    2. 分块策略 — 固定大小/句子边界/滑动窗口，各有适用场景")
        print("    3. chunk_overlap 保证上下文不丢失")
        print("    4. RAG 构建器 — 从原始文档到可查询知识库的完整流程")
        print("    5. 元数据随文档块存储，便于来源追溯")

    except Exception as e:
        print(f"\n  ❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
