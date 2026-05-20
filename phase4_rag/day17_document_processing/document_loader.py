"""
document_loader.py — 文档加载与分块

功能：
1. 加载多种格式文档（TXT、Markdown、Python代码、JSON）
2. 智能文档分块策略（固定大小 / 句子边界 / 滑动窗口）
3. 中文友好的分块处理

设计原则：零 LangChain 依赖，纯 Python 实现
"""
import re
from typing import List, Dict
from pathlib import Path


class TextLoader:
    """纯文本加载器 — 支持 TXT、Markdown、代码文件"""

    @staticmethod
    def load(file_path: str) -> str:
        """加载任意文本文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def load_python(file_path: str) -> str:
        """加载 Python 文件（可选择性去注释）"""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


class DocumentChunker:
    """智能文档分块器 — 多种分块策略"""

    def __init__(self, chunk_size: int = 300, chunk_overlap: int = 50):
        self.chunk_size = chunk_size           # 每个块的目标字符数
        self.chunk_overlap = chunk_overlap     # 块之间的重叠字符数

    def chunk_by_fixed_size(self, text: str) -> List[str]:
        """固定大小分块 — 简单但会在句子中间切断"""
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])
            start = end - self.chunk_overlap  # 重叠部分
        return chunks

    def chunk_by_sentence(self, text: str) -> List[str]:
        """按句子边界分块 — 中文友好，尽量在句号/换行处切分"""
        # 按句子分隔符拆分
        sentences = re.split(r"(?<=[。！？\n])\s*", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        current_chunk = ""
        for sentence in sentences:
            # 如果加上当前句子不超过块大小，则追加
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += sentence
            else:
                # 当前块已满，保存并开始新块
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        # 最后一个块
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def chunk_by_sliding_window(self, text: str) -> List[str]:
        """滑动窗口分块 — 每步移动 step 个字符，保证重叠"""
        chunks = []
        step = self.chunk_size - self.chunk_overlap
        for i in range(0, len(text), step):
            chunk = text[i:i + self.chunk_size]
            if len(chunk) >= 20:  # 过滤太短的块
                chunks.append(chunk)
            if i + self.chunk_size >= len(text):
                break
        return chunks

    def chunk_with_metadata(self, text: str, source: str = "",
                            strategy: str = "sentence") -> List[Dict]:
        """分块并附带元数据 — 完整的分块输出"""
        if strategy == "fixed":
            chunks = self.chunk_by_fixed_size(text)
        elif strategy == "sliding":
            chunks = self.chunk_by_sliding_window(text)
        else:
            chunks = self.chunk_by_sentence(text)

        return [
            {
                "content": chunk,
                "metadata": {
                    "source": source,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "char_count": len(chunk),
                }
            }
            for i, chunk in enumerate(chunks)
        ]


# ==================== 演示 ====================

def demo_loading():
    """演示文档加载和分块"""
    print("=" * 60)
    print("  文档加载与分块演示")
    print("=" * 60)

    # 创建示例文档
    sample_text = (
        "人工智能（AI）是计算机科学的一个重要分支。它致力于创造能够模拟人类智能的系统。\n\n"
        "深度学习是机器学习的一个子领域。它使用多层人工神经网络来学习数据的层次化表示。"
        "卷积神经网络（CNN）在图像识别任务中表现出色，而循环神经网络（RNN）适合处理序列数据。\n\n"
        "2017年，Google提出了Transformer架构。这个基于自注意力机制的模型彻底改变了自然语言处理领域。"
        "BERT和GPT系列模型都基于Transformer架构。GPT-4是OpenAI最新的多模态大语言模型。\n\n"
        "RAG（检索增强生成）是一种结合信息检索和文本生成的技术。它先检索相关文档再交给LLM生成答案。"
        "这种方法能有效减少模型幻觉，提高答案的准确性和可靠性。"
    )

    chunker = DocumentChunker(chunk_size=150, chunk_overlap=30)

    # 固定大小分块
    print("\n📋 策略 1: 固定大小分块 (size=150, overlap=30)")
    chunks = chunker.chunk_by_fixed_size(sample_text)
    for i, chunk in enumerate(chunks):
        print(f"  块 {i}: [{len(chunk)}字符] {chunk[:80]}...")

    # 句子边界分块
    print(f"\n📋 策略 2: 句子边界分块")
    chunks = chunker.chunk_by_sentence(sample_text)
    for i, chunk in enumerate(chunks):
        print(f"  块 {i}: [{len(chunk)}字符] {chunk[:80]}...")

    # 带元数据的分块
    print(f"\n📋 策略 3: 带元数据分块")
    results = chunker.chunk_with_metadata(sample_text, source="ai_overview.txt")
    for r in results:
        print(f"  块 {r['metadata']['chunk_index']}/{r['metadata']['total_chunks']}: "
              f"[{r['metadata']['char_count']}字符] {r['content'][:60]}...")


if __name__ == "__main__":
    demo_loading()
