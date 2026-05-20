"""
Day19: RAG 评估指标体系 — 从零实现核心评估指标（不依赖 RAGAS 库）

本模块实现了两套评估器:
1. RAGEvaluator: 评估最终回答质量（忠实度、相关性、完整性）
2. RetrievalEvaluator: 评估检索阶段质量（Precision@K, Recall@K, MRR, NDCG）

设计理念: 不使用外部 RAGAS 库，用 LLM 和向量计算从零实现每个指标，
          帮助学习者理解评估指标的本质而非仅仅是调用 API。
"""

import sys
from pathlib import Path
import os
import json
from typing import Any

# ==================== 导入公共配置 ====================
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # 将项目根目录加入 sys.path
from config import (  # 从公共配置导入所需变量
    OPENAI_API_KEY,    # API 密钥
    OPENAI_BASE_URL,   # API 请求地址
    OPENAI_MODEL,      # 大模型名称
    HF_ENDPOINT,       # HuggingFace 镜像地址（国内加速）
)

import numpy as np  # 用于向量运算（余弦相似度、NDCG 计算）
from openai import OpenAI  # OpenAI 兼容客户端，调用 LLM 进行评估判断


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """计算两个向量的余弦相似度（用于衡量向量间的语义接近程度）"""
    # 将输入列表转为 numpy 数组，便于向量化计算
    a: np.ndarray = np.array(vec_a)  # 向量 A
    b: np.ndarray = np.array(vec_b)  # 向量 B
    # 计算余弦相似度: dot(a,b) / (|a| * |b|)，加 1e-8 防止除零
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


# ==================== RAG 回答质量评估器 ====================
class RAGEvaluator:
    """
    RAG 评估器 — 从零实现 RAG 回答质量的核心评估指标

    评估三个维度:
    1. Faithfulness（忠实度）: 回答是否严格基于提供的文档，有无幻觉
    2. Relevance（文档相关性）: 检索到的文档是否与用户问题相关
    3. Completeness（完整性）: 回答是否覆盖了文档中的关键信息
    """

    def __init__(self) -> None:
        """初始化评估器，创建 LLM 客户端和向量模型"""
        # 创建 OpenAI 兼容的 LLM 客户端，用于基于 LLM 的判断类评估
        self.client: OpenAI = OpenAI(
            api_key=OPENAI_API_KEY,   # API 密钥（从环境变量读取）
            base_url=OPENAI_BASE_URL, # API 地址
        )
        # 设置 HuggingFace 镜像端点在导入 sentence-transformers 之前
        os.environ["HF_ENDPOINT"] = HF_ENDPOINT  # 使用国内镜像加速模型下载
        from sentence_transformers import SentenceTransformer  # 延迟导入，确保环境变量生效
        # 加载向量化模型，用于计算文档相关性
        self.embedding_model: SentenceTransformer = SentenceTransformer(
            "BAAI/bge-small-zh-v1.5"  # 中文小模型，速度快且效果不错
        )

    # ----------------------------------------------------------------
    def evaluate_faithfulness(self, answer: str, context_docs: list[str]) -> dict[str, Any]:
        """
        评估忠实度（Faithfulness）—— 回答是否完全基于提供的文档

        评估流程:
        1. 用 LLM 提取回答中的所有「断言/声明」（claims）
        2. 逐条检查每一条声明是否可以从 context_docs 中找到支撑
        3. 计算: 忠实度 = 有支撑的声明数 / 总声明数

        参数:
            answer: RAG 系统生成的回答文本
            context_docs: 检索返回的文档列表（作为回答的参考依据）

        返回:
            包含 score、supported_claims、unsupported_claims 的字典
        """
        # 第一步: 用 LLM 提取回答中的所有事实性声明
        extract_prompt: str = f"""请从以下回答中提取所有事实性声明（claims）。
每条声明应该是一个可验证的、独立的事实陈述。
以 JSON 数组格式返回，每个元素是一个声明字符串。

回答:
{answer}

请只返回 JSON 数组，不要包含其他文字。"""

        # 调用 LLM 提取声明
        extract_response = self.client.chat.completions.create(
            model=OPENAI_MODEL,            # 使用的模型
            messages=[{"role": "user", "content": extract_prompt}],  # 提示词
            temperature=0.0,               # temperature=0 确保输出稳定
        )
        claims_text: str = extract_response.choices[0].message.content.strip()  # 获取返回文本

        # 解析 LLM 返回的 JSON 声明列表
        try:
            claims: list[str] = json.loads(claims_text)  # 尝试解析 JSON 数组
        except json.JSONDecodeError:
            # 如果解析失败（LLM 格式不规矩），回退为按句号分句
            claims = [s.strip() + "。" for s in answer.split("。") if s.strip()]

        # 如果没有提取到声明，返回空结果
        if not claims:
            return {"score": 1.0, "supported_claims": [], "unsupported_claims": []}

        # 第二步: 用 LLM 逐条检查每个声明是否有文档支撑
        # 将文档拼接成参考文本
        context_text: str = "\n---\n".join(context_docs)  # 文档之间用分隔线隔开

        supported: list[str] = []    # 有支撑的声明
        unsupported: list[str] = []  # 无支撑的声明（可能是幻觉）

        for claim in claims:
            # 构造提示词: 让 LLM 判断这一条声明是否被文档支持
            check_prompt: str = f"""请判断下面这条声明是否可以从提供的参考文档中推断出来。
只回答 "YES" 或 "NO"。

参考文档:
{context_text}

声明: {claim}

这条声明是否被文档支持？（YES/NO）:"""

            check_response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": check_prompt}],
                temperature=0.0,          # 零温度确保判断一致
                max_tokens=5,             # 只需要 YES 或 NO
            )
            verdict: str = check_response.choices[0].message.content.strip().upper()  # 获取判断结果

            # 根据判断结果分类声明
            if "YES" in verdict:
                supported.append(claim)  # 有支撑
            else:
                unsupported.append(claim)  # 无支撑

        # 计算忠实度得分: 有支撑的比例
        score: float = len(supported) / len(claims) if claims else 0.0
        return {
            "score": round(score, 4),          # 保留 4 位小数
            "supported_claims": supported,      # 有支撑的声明列表
            "unsupported_claims": unsupported,  # 无支撑的声明列表
        }

    # ----------------------------------------------------------------
    def evaluate_relevance(self, query: str, context_docs: list[str]) -> dict[str, Any]:
        """
        评估文档相关性（Context Relevance）—— 检索到的文档与查询的相关程度

        评估方法: 将 query 向量化，与每个 doc 向量计算余弦相似度，
                  取平均值作为整体相关性得分

        参数:
            query: 用户的原始查询
            context_docs: 检索返回的文档列表

        返回:
            包含 mean_score、per_doc_scores、min_score、max_score 的字典
        """
        if not context_docs:
            return {"mean_score": 0.0, "per_doc_scores": [], "min_score": 0.0, "max_score": 0.0}

        # 将查询向量化，得到查询的语义表示
        query_embedding: np.ndarray = self.embedding_model.encode([query])[0]  # 返回 (1, dim) 取第一行

        # 将每个文档向量化
        doc_embeddings: np.ndarray = self.embedding_model.encode(context_docs)  # 返回 (n_docs, dim)

        # 逐一计算每个文档与查询的余弦相似度
        per_doc_scores: list[float] = []
        for i, doc_emb in enumerate(doc_embeddings):
            sim: float = cosine_similarity(
                query_embedding.tolist(),  # 查询向量 -> 列表
                doc_emb.tolist(),          # 文档向量 -> 列表
            )
            per_doc_scores.append(round(sim, 4))  # 保留 4 位小数后加入结果列表

        # 计算整体统计指标
        mean_score: float = round(float(np.mean(per_doc_scores)), 4)  # 平均相关性
        min_score: float = round(float(np.min(per_doc_scores)), 4)    # 最低相关性
        max_score: float = round(float(np.max(per_doc_scores)), 4)    # 最高相关性

        return {
            "mean_score": mean_score,        # 平均相关性（整体检索质量）
            "per_doc_scores": per_doc_scores,  # 每个文档的单独得分
            "min_score": min_score,          # 最低分（最不相关的文档）
            "max_score": max_score,          # 最高分（最相关的文档）
        }

    # ----------------------------------------------------------------
    def evaluate_completeness(self, query: str, answer: str, context_docs: list[str]) -> dict[str, Any]:
        """
        评估完整性（Answer Completeness）—— 回答是否覆盖了文档中的关键信息

        评估方法: 用 LLM 先提取文档的关键信息点，再检查这些信息点是否在回答中出现

        参数:
            query: 用户的原始查询
            answer: RAG 系统生成的回答
            context_docs: 检索返回的文档列表（作为完整信息的来源）

        返回:
            包含 score、covered_points、missed_points 的字典
        """
        # 将所有文档拼接为参考文本
        context_text: str = "\n---\n".join(context_docs)  # 文档拼接

        # 第一步: 用 LLM 从文档中提取针对当前问题的关键信息点
        extract_points_prompt: str = f"""请从以下参考文档中，提取出回答用户问题所需的关键信息点。
以 JSON 数组格式返回，每个元素是一个关键信息点。

用户问题: {query}

参考文档:
{context_text}

请只返回 JSON 数组格式的关键信息点列表。每个信息点是一个简短的陈述句。"""

        extract_response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": extract_points_prompt}],
            temperature=0.0,
        )
        points_text: str = extract_response.choices[0].message.content.strip()  # 获取返回文本

        # 解析 LLM 返回的关键信息点列表
        try:
            key_points: list[str] = json.loads(points_text)  # 尝试解析 JSON
        except json.JSONDecodeError:
            key_points = []  # 解析失败则给空列表

        if not key_points:
            return {"score": 1.0, "covered_points": [], "missed_points": []}

        # 第二步: 对每个关键信息点，用 LLM 判断它是否在回答中被覆盖
        covered: list[str] = []  # 被覆盖的信息点
        missed: list[str] = []   # 缺失的信息点

        for point in key_points:
            # 构造判断提示词
            cover_prompt: str = f"""请判断以下关键信息点是否在回答中被提及或包含。
只回答 "YES" 或 "NO"。

关键信息点: {point}

回答: {answer}

是否包含？（YES/NO）:"""

            cover_response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": cover_prompt}],
                temperature=0.0,
                max_tokens=5,
            )
            verdict: str = cover_response.choices[0].message.content.strip().upper()

            if "YES" in verdict:
                covered.append(point)  # 回答覆盖了该信息点
            else:
                missed.append(point)   # 回答遗漏了该信息点

        # 计算完整性得分
        score: float = len(covered) / len(key_points) if key_points else 0.0
        return {
            "score": round(score, 4),     # 完整性得分
            "covered_points": covered,    # 已覆盖的信息点
            "missed_points": missed,      # 遗漏的信息点
        }

    # ----------------------------------------------------------------
    def evaluate_all(self, query: str, answer: str, context_docs: list[str]) -> dict[str, Any]:
        """
        一站式评估 — 同时输出忠实度、相关性、完整性的综合评估结果

        参数:
            query: 用户查询
            answer: 生成的回答
            context_docs: 检索到的文档

        返回:
            包含所有评估指标的综合字典
        """
        print("=" * 60)  # 打印分隔线
        print(f"正在评估 RAG 输出质量...")
        print(f"查询: {query}")
        print(f"回答长度: {len(answer)} 字符")
        print(f"文档数量: {len(context_docs)} 篇")
        print("=" * 60)

        # 分别计算三个维度的指标
        faithfulness: dict = self.evaluate_faithfulness(answer, context_docs)  # 忠实度
        relevance: dict = self.evaluate_relevance(query, context_docs)         # 文档相关性
        completeness: dict = self.evaluate_completeness(query, answer, context_docs)  # 完整性

        # 组装综合结果
        result: dict[str, Any] = {
            "query": query,                # 原始查询
            "faithfulness": faithfulness,  # 忠实度详情
            "relevance": relevance,        # 相关性详情
            "completeness": completeness,  # 完整性详情
            "summary": {                   # 摘要信息
                "faithfulness_score": faithfulness["score"],    # 忠实度得分
                "relevance_score": relevance["mean_score"],     # 相关性均分
                "completeness_score": completeness["score"],    # 完整性得分
                "overall_score": round(                        # 综合得分（算术平均）
                    (faithfulness["score"] + relevance["mean_score"] + completeness["score"]) / 3, 4
                ),
            },
        }
        return result


# ==================== 检索质量评估器 ====================
class RetrievalEvaluator:
    """
    检索质量评估器 — 评估检索阶段的性能

    支持四种经典信息检索指标:
    1. Precision@K: 前 K 个结果中相关结果的比例
    2. Recall@K: 前 K 个结果覆盖了多少相关文档
    3. MRR (Mean Reciprocal Rank): 第一个相关结果的排名的倒数均值
    4. NDCG@K (Normalized Discounted Cumulative Gain): 考虑排名的相关性评估

    这些指标不依赖 LLM，只需知道哪些文档是相关的（ground truth）
    """

    def __init__(self) -> None:
        """初始化检索评估器（当前不需要额外资源）"""
        pass  # 检索指标的运算无需额外初始化

    # ----------------------------------------------------------------
    def precision_at_k(self, retrieved: list[str], relevant: list[str], k: int = 5) -> float:
        """
        计算 Precision@K — 检索结果前 K 个中相关文档的比例

        公式: P@K = |前K个结果 ∩ 相关文档| / K

        参数:
            retrieved: 检索系统返回的文档 ID 列表（按排名降序）
            relevant: 标注的与查询相关的文档 ID 列表（ground truth）
            k: 只看前 K 个结果

        返回:
            Precision@K 值，范围 [0, 1]
        """
        if k <= 0:
            return 0.0  # K 必须为正数
        # 截取前 K 个检索结果
        top_k: list[str] = retrieved[:k]  # 取前 K 个（已按相关性排序）
        # 计算前 K 个结果中有多少是相关的
        relevant_set: set[str] = set(relevant)  # 转为集合，加速查找
        relevant_count: int = sum(1 for doc_id in top_k if doc_id in relevant_set)  # 计数
        return round(relevant_count / k, 4)  # 相关数 / K

    # ----------------------------------------------------------------
    def recall_at_k(self, retrieved: list[str], relevant: list[str], k: int = 5) -> float:
        """
        计算 Recall@K — 前 K 个结果中包含了多少相关文档

        公式: R@K = |前K个结果 ∩ 相关文档| / |相关文档|

        参数:
            retrieved: 检索系统返回的文档 ID 列表（按排名降序）
            relevant: 标注的相关文档 ID 列表
            k: 只看前 K 个结果

        返回:
            Recall@K 值，范围 [0, 1]
        """
        if k <= 0 or len(relevant) == 0:
            return 0.0  # K 必须为正，且需有相关文档
        # 截取前 K 个结果
        top_k: list[str] = retrieved[:k]  # 前 K 个检索结果
        relevant_set: set[str] = set(relevant)  # 相关文档集合
        # 统计前 K 中命中的相关文档数
        relevant_hit: int = sum(1 for doc_id in top_k if doc_id in relevant_set)
        return round(relevant_hit / len(relevant), 4)  # 命中数 / 总相关数

    # ----------------------------------------------------------------
    def mrr(self, queries_relevant: dict[str, list[str]], retrieved_list: dict[str, list[str]]) -> float:
        """
        计算 MRR (Mean Reciprocal Rank) — 第一个相关结果排名的倒数的均值

        公式: MRR = (1/|Q|) * SUM_q( 1 / rank_q )
        其中 rank_q 是查询 q 的第一个相关结果的排名位置（从 1 开始）

        参数:
            queries_relevant: {query_id: [相关文档ID列表], ...}
            retrieved_list: {query_id: [检索结果ID列表（按排名）], ...}

        返回:
            MRR 值，范围 [0, 1]，越接近 1 说明第一个相关结果越靠前
        """
        if not queries_relevant or not retrieved_list:
            return 0.0  # 空输入

        reciprocal_ranks: list[float] = []  # 存储每个查询的倒数排名

        for query_id, relevant_docs in queries_relevant.items():
            # 获取该查询的检索结果
            retrieved_docs: list[str] = retrieved_list.get(query_id, [])
            relevant_set: set[str] = set(relevant_docs)
            found: bool = False  # 是否找到了相关文档

            # 按排名逐个检查
            for rank_idx, doc_id in enumerate(retrieved_docs, start=1):
                if doc_id in relevant_set:
                    reciprocal_ranks.append(1.0 / rank_idx)  # 倒数排名
                    found = True
                    break  # 找到第一个就停止

            if not found:
                reciprocal_ranks.append(0.0)  # 没有任何相关文档，MRR 贡献为 0

        # 计算所有查询的均值
        return round(float(np.mean(reciprocal_ranks)), 4)  # 平均倒数排名

    # ----------------------------------------------------------------
    def ndcg_at_k(self, retrieved: list[str], relevant: list[str], k: int = 5) -> float:
        """
        计算 NDCG@K (Normalized Discounted Cumulative Gain) — 考虑排名位置的相关性评估

        DCG@K = SUM_{i=1..K}( rel_i / log2(i+1) )
        IDCG@K = 理想排序下的 DCG@K（相关文档全部排在最前面）
        NDCG@K = DCG@K / IDCG@K

        参数:
            retrieved: 检索系统返回的文档 ID 列表（按排名降序）
            relevant: 标注的相关文档 ID 列表（所有相关文档同等重要，rel=1）

        返回:
            NDCG@K 值，范围 [0, 1]
        """
        if k <= 0 or len(relevant) == 0:
            return 0.0  # 无相关内容时 NDCG 为 0

        relevant_set: set[str] = set(relevant)  # 相关文档集合
        top_k: list[str] = retrieved[:k]  # 取前 K 个

        # ---- 计算 DCG@K（实际排序的折损累计增益） ----
        dcg: float = 0.0  # 累计折损增益
        for i, doc_id in enumerate(top_k, start=1):
            if doc_id in relevant_set:
                # 相关度为 1，位置为 i，折损因子为 log2(i+1)
                dcg += 1.0 / np.log2(i + 1)  # 越靠后的位置贡献越小

        # ---- 计算 IDCG@K（理想排序的 DCG） ----
        # 理想情况: 所有相关文档排在前面
        ideal_relevant_count: int = min(len(relevant_set), k)  # 理想前 K 中最多有这些相关文档
        idcg: float = 0.0  # 理想 DCG
        for i in range(1, ideal_relevant_count + 1):
            idcg += 1.0 / np.log2(i + 1)  # 所有被检索的相关文档都在最前面

        # NDCG = DCG / IDCG（如果 IDCG 为 0，则返回 0）
        if idcg == 0:
            return 0.0
        return round(dcg / idcg, 4)  # 归一化后的折损累计增益

    # ----------------------------------------------------------------
    def evaluate_all(
        self,
        retrieved: list[str],
        relevant: list[str],
        k_values: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        一站式检索评估 — 同时计算多个 K 值下的所有指标

        参数:
            retrieved: 检索结果文档 ID 列表
            relevant: 相关文档 ID 列表
            k_values: 要评估的 K 值列表，默认 [1, 3, 5, 10]

        返回:
            包含所有 K 值下所有指标的字典
        """
        if k_values is None:
            k_values = [1, 3, 5, 10]  # 默认评估 Top-1,3,5,10

        result: dict[str, Any] = {"retrieved_count": len(retrieved), "relevant_count": len(relevant)}

        for k in k_values:
            # 对于每个 K 值分别计算各指标
            p: float = self.precision_at_k(retrieved, relevant, k)  # Precision@K
            r: float = self.recall_at_k(retrieved, relevant, k)     # Recall@K
            n: float = self.ndcg_at_k(retrieved, relevant, k)       # NDCG@K
            result[f"P@{k}"] = p   # 存储 Precision@K
            result[f"R@{k}"] = r   # 存储 Recall@K
            result[f"NDCG@{k}"] = n  # 存储 NDCG@K

        return result


# ==================== 模块自测代码 ====================
if __name__ == "__main__":
    """
    自测代码: 运行后可验证所有指标的计算逻辑是否正常
    """
    print("=== RAG 评估指标模块自测 ===\n")

    # ---- 测试检索评估器（不需要 LLM 和网络） ----
    ret_eval = RetrievalEvaluator()  # 实例化检索评估器

    # 模拟数据: 8 个检索结果 + 4 个相关文档
    retrieved_ids: list[str] = [  # 检索系统按相关性排序返回
        "doc_3", "doc_1", "doc_7", "doc_2", "doc_5", "doc_9", "doc_4", "doc_8",
    ]
    relevant_ids: list[str] = ["doc_1", "doc_2", "doc_3", "doc_4"]  # 标注的相关文档

    # 计算并打印各指标
    ret_result: dict = ret_eval.evaluate_all(retrieved_ids, relevant_ids)
    print("检索评估结果:")
    for metric, value in ret_result.items():
        print(f"  {metric}: {value}")  # 逐项打印指标名和值

    print("\n自测完成! (RAGEvaluator 的 LLM 依赖请通过 example.py 测试)")
