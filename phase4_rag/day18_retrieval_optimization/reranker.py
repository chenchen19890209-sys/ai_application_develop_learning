"""
重排序（Reranking）模块
=======================
Day 18 核心知识点：交叉编码器重排序 + LLM 重排序

在混合检索得到候选文档后，重排序（Reranking）作为精排阶段：
1. Cross-Encoder Reranker：输入 (query, doc) 对，输出精细的相关度分数
2. LLM Reranker：用大语言模型理解查询意图，评估每篇文档的相关性

为什么需要重排序？
- 初排（BM25/向量检索）速度快但精度有限 → 召回阶段
- 精排（Reranker）速度较慢但精度高 → 只对 Top-K 候选重排序
- 这是一种经典的 "粗排-精排" 两阶段 pipeline

用法:
    reranker = CrossEncoderReranker()
    reranked = reranker.rerank(query, candidates, top_k=3)
"""

# ==================== 路径配置 ====================
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，以便导入顶层 config.py
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# ==================== 公共配置导入 ====================
from config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    HF_ENDPOINT,
    TEMPERATURE,
    MAX_TOKENS,
)

# ==================== 标准库导入 ====================
import os
import time
from typing import List, Dict, Any, Optional

# ==================== 关键：在导入 sentence-transformers 之前设置 HF 镜像 ====================
os.environ["HF_ENDPOINT"] = HF_ENDPOINT

# ==================== 第三方库导入 ====================
from sentence_transformers import CrossEncoder  # 交叉编码器，用于精细相关度计算
from openai import OpenAI  # OpenAI 兼容客户端，用于 LLM 重排序

# ==================== LLM 客户端 ====================
# 使用 OpenAI 兼容接口初始化客户端（此处指向 DeepSeek）
_llm_client: Optional[OpenAI] = None


def _get_llm_client() -> OpenAI:
    """
    获取 LLM 客户端单例（懒加载）

    懒加载的好处：
    - 只在需要时初始化（CrossEncoderReranker 不需要 LLM 客户端）
    - 避免在模块导入时联网验证 API Key
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
        )
    return _llm_client


# ==================== 交叉编码器重排序 ====================

class CrossEncoderReranker:
    """
    交叉编码器重排序 — 精细计算查询和文档的相关度

    工作原理（以 BGE-Reranker 为例）：

    双编码器（Bi-Encoder）     vs      交叉编码器（Cross-Encoder）
    ┌─────────┐ ┌──────────┐         ┌──────────────────────────┐
    │  Query  │ │ Document │         │  [CLS] Query [SEP] Doc   │
    │ Encoder │ │ Encoder  │         │                          │
    └────┬─────┘ └────┬─────┘         │      Transformer Layers   │
         │            │               │      (cross-attention)   │
         ▼            ▼               └────────────┬─────────────┘
       q_vec       d_vec                           ▼
            \      /                     relevance_score [0, 1]
           similarity
          (点积/余弦)

    双编码器：独立编码 query 和 doc，速度快但交互弱
    交叉编码器：将 query 和 doc 拼接后一起输入，通过 cross-attention 深度交互，精度高但速度慢

    因此交叉编码器适合作为"精排"阶段，只对少量候选文档重排序。
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-base") -> None:
        """
        初始化交叉编码器重排序器

        Args:
            model_name: HuggingFace 重排序模型名称
                        BAAI/bge-reranker-base 是 BGE 系列的中文重排序模型（约 1.1GB）
                        另有 bge-reranker-large（约 4.5GB，精度更高但更慢）
                        和 bge-reranker-v2-m3（多语言版本）
        """
        self.model_name: str = model_name
        print(f"[CrossEncoder] 正在加载重排序模型: {model_name} ...")

        # 加载 CrossEncoder 模型
        # CrossEncoder 返回 logits（未归一化的分数），通过 sigmoid 可转为概率
        self.model = CrossEncoder(model_name)
        print(f"[CrossEncoder] 模型加载完成")

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        使用交叉编码器对候选文档进行重排序

        流程：
        1. 构造 (query, doc) 对列表
        2. 用 CrossEncoder 对每对打分
        3. 按分数降序排列，返回 top_k 结果

        Args:
            query: 查询文本（中文）
            documents: 候选文档列表（通常来自混合检索的 Top-K 结果）
            top_k: 返回的文档数量，默认 3

        Returns:
            重排序结果列表，每项包含：
                - "rank": 重排序后排名（1-based）
                - "score": 相关度分数（logits，越高越相关）
                - "document": 文档文本
                - "original_index": 原始候选列表中的索引
        """
        # 步骤 1：构造 (query, document) 配对列表
        # CrossEncoder 的输入格式：[query, doc_text] 的列表
        pairs: List[List[str]] = [[query, doc] for doc in documents]

        # 步骤 2：批量计算相关度分数
        # predict() 返回每个 pair 的相关度分数列表
        # show_progress_bar=True 显示计算进度
        # 分数是模型输出的 logits 值（未归一化），正数表示相关，负数表示不相关
        scores: List[float] = self.model.predict(
            pairs,
            show_progress_bar=True
        )

        # 步骤 3：按分数降序排序
        # enumerate 生成 (原始索引, 分数) 对
        ranked: List[Any] = sorted(
            enumerate(scores),
            key=lambda x: x[1],  # 按分数排序
            reverse=True  # 降序：分数高的在前
        )

        # 步骤 4：构建统一格式的结果列表
        results: List[Dict[str, Any]] = []
        for rank, (orig_idx, score) in enumerate(ranked[:top_k], start=1):
            results.append({
                "rank": rank,  # 重排序后的排名
                "score": round(float(score), 4),  # 相关度分数（logits）
                "document": documents[orig_idx],  # 原始文档文本
                "original_index": orig_idx,  # 原始候选列表中的位置
            })

        return results

    def batch_rerank(
        self,
        queries: List[str],
        documents_list: List[List[str]],
        top_k: int = 3
    ) -> List[List[Dict[str, Any]]]:
        """
        批量重排序（对多个查询同时处理）

        使用场景：离线评估、批量处理等

        Args:
            queries: 查询文本列表
            documents_list: 每个查询对应的候选文档列表
            top_k: 每个查询返回的文档数量

        Returns:
            每个查询的重排序结果列表
        """
        all_results: List[List[Dict[str, Any]]] = []
        for query, docs in zip(queries, documents_list):
            result = self.rerank(query, docs, top_k=top_k)
            all_results.append(result)
        return all_results


# ==================== LLM 重排序 ====================

class LLMReranker:
    """
    LLM 重排序 — 用大语言模型评估文档相关性

    工作原理：
    1. 将查询和每篇候选文档一起发给 LLM
    2. LLM 根据深度语义理解，判断文档与查询的相关程度
    3. 收集 LLM 的打分结果，按分数排序

    优点：
    - 利用 LLM 强大的语言理解能力进行精细判断
    - 可以处理复杂的语义相关性（如反讽、隐喻、专业领域知识）

    缺点：
    - 速度最慢（每篇文档都要调用一次 LLM API）
    - 有 API 调用成本
    - 对提示词（prompt）敏感

    适用场景：
    - 候选文档数量少（通常 3~5 篇）的最终精排
    - 对检索质量要求极高的场景
    """

    def __init__(self) -> None:
        """
        初始化 LLM 重排序器
        """
        # 获取 LLM 客户端（懒加载）
        self.client: OpenAI = _get_llm_client()
        # 使用的模型名称
        self.model: str = OPENAI_MODEL
        # LLM 温度参数（relevance judgment 需要确定性输出）
        self.temperature: float = 0.0

    def _build_rerank_prompt(self, query: str, documents: List[str]) -> str:
        """
        构造 LLM 重排序的提示词

        思路：
        - 告诉 LLM 它的角色（信息检索专家）
        - 给出明确的打分标准（0-10 分制）
        - 列出所有候选文档（编号区分）
        - 要求输出结构化的 JSON 格式结果

        Args:
            query: 用户查询
            documents: 候选文档列表

        Returns:
            构造好的提示词字符串
        """
        # 将文档编号并拼接
        docs_str: str = ""
        for i, doc in enumerate(documents, start=1):
            # 限制每篇文档最多展示 300 字符（避免 prompt 过长）
            truncated: str = doc[:300] + ("..." if len(doc) > 300 else "")
            docs_str += f"\n文档 {i}: {truncated}"

        # 构造完整提示词
        prompt: str = f"""你是一个信息检索评估专家。请根据用户查询，评估以下文档的相关性。

用户查询: {query}

候选文档:
{docs_str}

请对每篇文档从 0 到 10 打分，标准如下:
- 10 分: 完全匹配查询意图，包含查询所需的核心信息
- 7-9 分: 高度相关，包含大量有用信息
- 4-6 分: 部分相关，有一定参考价值
- 1-3 分: 略微相关，信息有限
- 0 分: 完全不相关

请严格按照以下 JSON 格式返回结果，只返回 JSON，不要有其他文字:
{{"scores": [{{"doc_id": 1, "score": 8, "reason": "简要理由"}}, ...]}}

注意: doc_id 对应上面的文档编号，scores 数组必须包含所有文档的评分。"""

        return prompt

    def _parse_rerank_response(
        self,
        response: str,
        num_docs: int
    ) -> List[Dict[str, Any]]:
        """
        解析 LLM 的重排序响应

        Args:
            response: LLM 返回的文本
            num_docs: 候选文档总数（用于验证解析完整性）

        Returns:
            解析后的评分列表，每项包含 doc_id、score、reason
        """
        import json

        # 尝试从响应中提取 JSON（LLM 可能在 JSON 前后添加额外文本）
        # 查找第一个 { 和最后一个 } 之间的内容
        try:
            # 直接尝试解析
            parsed = json.loads(response)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取 JSON 块
            start: int = response.find("{")
            end: int = response.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    parsed = json.loads(response[start:end])
                except json.JSONDecodeError:
                    # 最终回退：返回默认空评分
                    print(f"[LLMReranker] 警告: 无法解析 LLM 响应，使用默认评分")
                    return [{"doc_id": i, "score": 0, "reason": "解析失败"}
                            for i in range(1, num_docs + 1)]
            else:
                return [{"doc_id": i, "score": 0, "reason": "解析失败"}
                        for i in range(1, num_docs + 1)]

        # 提取 scores 数组
        scores_list: List[dict] = parsed.get("scores", [])
        return scores_list

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        使用 LLM 对候选文档进行重排序

        流程：
        1. 构造重排序 prompt
        2. 调用 LLM API 获取评分
        3. 解析 LLM 响应
        4. 按分数排序返回 top_k

        Args:
            query: 查询文本（中文）
            documents: 候选文档列表
            top_k: 返回的文档数量，默认 3

        Returns:
            重排序结果列表，每项包含：
                - "rank": 重排序后排名（1-based）
                - "score": LLM 打分（0-10）
                - "document": 文档文本
                - "reason": LLM 给出的理由
                - "original_index": 原始候选列表中的索引
        """
        if not documents:
            return []

        # 步骤 1：构造提示词
        prompt: str = self._build_rerank_prompt(query, documents)

        # 步骤 2：调用 LLM API
        print(f"[LLMReranker] 正在请求 LLM 评估 {len(documents)} 篇文档...")
        start_time: float = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的信息检索评估专家。请只返回 JSON 格式的结果。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,  # 确定性输出
                max_tokens=MAX_TOKENS,
            )

            # 提取 LLM 返回的文本内容
            response_text: str = response.choices[0].message.content or ""

            elapsed: float = time.time() - start_time
            print(f"[LLMReranker] LLM 响应完成，耗时 {elapsed:.2f} 秒")

        except Exception as e:
            print(f"[LLMReranker] 错误: LLM API 调用失败: {e}")
            return []

        # 步骤 3：解析 LLM 响应中的评分
        scores_list: List[Dict[str, Any]] = self._parse_rerank_response(
            response_text, len(documents)
        )

        # 步骤 4：按 LLM 评分降序排序
        # 注意：scores_list 中的 doc_id 是 1-based
        sorted_scores: List[dict] = sorted(
            scores_list,
            key=lambda x: x.get("score", 0),
            reverse=True  # 降序：分数高的在前
        )

        # 步骤 5：构建统一格式的结果列表
        results: List[Dict[str, Any]] = []
        for rank, score_item in enumerate(sorted_scores[:top_k], start=1):
            doc_id: int = score_item.get("doc_id", 0)
            # doc_id 是 1-based，转换为 0-based 索引
            doc_idx: int = doc_id - 1 if doc_id > 0 else 0

            results.append({
                "rank": rank,  # 重排序后的排名
                "score": score_item.get("score", 0),  # LLM 打分 (0-10)
                "reason": score_item.get("reason", ""),  # LLM 给出的打分理由
                "document": documents[doc_idx] if 0 <= doc_idx < len(documents) else "",
                "original_index": doc_idx,  # 原始候选列表中的位置
            })

        return results


# ==================== 模块演示入口 ====================

def main() -> None:
    """
    重排序模块的独立演示

    展示 CrossEncoder 和 LLM 两种重排序方式的效果差异
    """
    print("=" * 70)
    print("  Day 18: 重排序演示 — CrossEncoder + LLM Reranker")
    print("=" * 70)

    # 模拟来自混合检索的候选文档（Top-6）
    query: str = "Python 在机器学习中的应用"
    candidates: List[str] = [
        "Python 是一种广泛用于数据科学和机器学习的编程语言，拥有丰富的库如 NumPy、pandas、scikit-learn。",
        "FastAPI 是一个现代高性能的 Python Web 框架，支持自动生成 API 文档。",
        "深度学习使用多层神经网络来学习数据的层次化表示，在图像识别和自然语言处理方面表现出色。",
        "Python 是 Guido van Rossum 在 1991 年创造的通用编程语言。",
        "机器学习是人工智能的一个分支，它使计算机能够从数据中学习。Python 是 ML 的首选语言。",
        "PyTorch 是 Facebook 开发的开源深度学习框架，广泛用于研究和工业界。",
    ]

    # 打印候选文档
    print(f"\n查询: \"{query}\"")
    print(f"\n候选文档（共 {len(candidates)} 篇）:")
    for i, doc in enumerate(candidates, start=1):
        print(f"  [{i}] {doc[:60]}...")

    # ==================== CrossEncoder 重排序 ====================
    print(f"\n{'='*70}")
    print("  1. CrossEncoder 重排序")
    print(f"{'='*70}")
    ce_reranker = CrossEncoderReranker()
    ce_results = ce_reranker.rerank(query, candidates, top_k=3)
    print(f"\n  CrossEncoder 重排序结果（Top-3）:")
    for item in ce_results:
        print(f"    #{item['rank']}: 分数={item['score']:.4f} "
              f"(原始索引[{item['original_index']}]) | {item['document'][:60]}...")

    # ==================== LLM 重排序 ====================
    print(f"\n{'='*70}")
    print("  2. LLM 重排序")
    print(f"{'='*70}")
    llm_reranker = LLMReranker()
    llm_results = llm_reranker.rerank(query, candidates, top_k=3)
    print(f"\n  LLM 重排序结果（Top-3）:")
    for item in llm_results:
        print(f"    #{item['rank']}: 分数={item['score']}/10 "
              f"(原始索引[{item['original_index']}]) | {item['document'][:60]}...")
        if item.get("reason"):
            print(f"         理由: {item['reason']}")

    # ==================== 对比总结 ====================
    print(f"\n{'='*70}")
    print("  重排序对比总结:")
    print("  • CrossEncoder: 速度快（本地推理），精度高，适合大多数场景")
    print("  • LLM Reranker: 速度慢（API 调用），理解深度更强，适合最终精排")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
