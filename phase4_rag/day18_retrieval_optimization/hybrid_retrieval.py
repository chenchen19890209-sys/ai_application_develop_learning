"""
混合检索（Hybrid Retrieval）模块
===============================
Day 18 核心知识点：BM25 稀疏检索 + 向量稠密检索 + RRF 融合

BM25 擅长精准关键词匹配（"苹果手机"必须出现"苹果"或"手机"），
向量检索擅长语义匹配（"智能手机"能匹配到"iPhone"），
混合检索 = 取两者之长，通过 RRF 算法融合排序结果。

用法:
    retriever = HybridRetriever()
    retriever.index(documents)
    results = retriever.search("查询文本", top_k=5)
"""

# ==================== 路径配置 ====================
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，以便导入顶层 config.py
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# ==================== 公共配置导入 ====================
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, HF_ENDPOINT

# ==================== 标准库导入 ====================
import os
from typing import List, Dict, Tuple, Optional, Any

# ==================== 关键：在导入 sentence-transformers 之前设置 HF 镜像 ====================
# 对于中国用户，HuggingFace 官方站可能无法直接访问，需要提前设置镜像端点
os.environ["HF_ENDPOINT"] = HF_ENDPOINT

# ==================== 第三方库导入 ====================
import chromadb  # ChromaDB 向量数据库
from chromadb.config import Settings as ChromaSettings  # ChromaDB 配置类
from sentence_transformers import SentenceTransformer  # 文本嵌入模型
from rank_bm25 import BM25Okapi  # BM25 稀疏检索算法
import jieba  # 中文分词库，用于 BM25 的文档分词

# ==================== 中文文档语料库 ====================
# 用于演示混合检索效果的示例文档集（至少 15 篇中文文档）
DEMO_DOCUMENTS: List[str] = [
    "Python 是一种解释型、面向对象的高级编程语言，由 Guido van Rossum 于 1991 年首次发布。",
    "机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下从数据中学习。",
    "深度学习使用多层神经网络来学习数据的层次化表示，在图像识别和自然语言处理方面表现出色。",
    "自然语言处理（NLP）是 AI 领域的重要分支，研究计算机与人类语言的交互。",
    "ChromaDB 是一个开源的向量数据库，专门用于存储和检索嵌入向量，适合 RAG 应用场景。",
    "RAG（检索增强生成）是一种将检索系统与生成模型结合的架构，可有效减少幻觉问题。",
    "BM25 是一种基于概率检索模型的排序函数，广泛用于搜索引擎的信息检索任务。",
    "Transformer 架构由 Vaswani 等人在 2017 年提出，彻底改变了自然语言处理领域。",
    "PyTorch 是 Facebook 开发的开源深度学习框架，以动态计算图和易用性著称。",
    "FastAPI 是一个现代高性能的 Python Web 框架，支持自动生成 API 文档和异步处理。",
    "向量数据库专门设计用于存储高维向量数据，支持高效的近似最近邻（ANN）搜索。",
    "大语言模型（LLM）是指参数量巨大的语言模型，如 GPT-4、ChatGLM 等，具有强大的文本生成能力。",
    "Embedding 技术将文本映射到低维稠密向量空间，语义相近的文本在向量空间中距离更近。",
    "HuggingFace 是全球最大的 AI 模型开源社区，提供了丰富的预训练模型和数据集。",
    "检索优化是提升 RAG 系统效果的关键步骤，包括混合检索、重排序和查询改写等技术。",
    "文本分块（Text Chunking）是 RAG 系统的基础预处理步骤，合理的分块策略可以显著提升检索质量。",
    "语义搜索基于向量相似度进行匹配，能够理解查询的真实意图而非仅匹配关键词。",
    "RRF（倒数排名融合）是一种无需训练就能融合多个检索结果排序的经典算法。",
]

# ==================== RRF 融合常量 ====================
RRF_K: int = 60  # RRF 算法的平滑参数，典型取值 60


# ==================== BM25 检索器 ====================

class BM25Retriever:
    """
    BM25 稀疏检索器 — 基于词频的关键词匹配

    BM25（Best Matching 25）是经典的 IR 排序算法，核心思想：
    1. 词频（TF）：查询词在文档中出现的次数越多，相关度越高（但有饱和机制）
    2. 逆文档频率（IDF）：查询词在越少的文档中出现，该词越有区分度
    3. 文档长度归一化：长文档有更高概率包含查询词，需要归一化

    优点：精准关键词匹配、可解释性强、无需 GPU
    缺点：无法理解同义词（如"电脑"和"计算机"被视为不同词）
    """

    def __init__(self) -> None:
        """
        初始化 BM25 检索器

        原理说明：
            - BM25 不需要训练或模型加载，仅在 index() 阶段构建统计索引
            - 使用 rank-bm25 库的 BM25Okapi 实现（Okapi BM25 是标准实现）
        """
        # 存储原始文档列表，用于检索后返回文本内容
        self.documents: List[str] = []
        # 分词后的文档列表（每个文档是一个 token 列表），供 BM25Okapi 使用
        self.tokenized_corpus: List[List[str]] = []
        # BM25Okapi 索引对象，在 index() 中实例化
        self.bm25: Optional[BM25Okapi] = None
        # 标记是否已完成索引构建
        self._is_indexed: bool = False

    def _tokenize(self, text: str) -> List[str]:
        """
        对单段文本进行中文分词

        Args:
            text: 待分词的文本字符串

        Returns:
            分词后的 token 列表
        """
        # 使用 jieba 进行中文分词（精确模式），jieba 会将"自然语言处理"切分为["自然", "语言", "处理"]
        return list(jieba.cut(text))

    def index(self, documents: List[str]) -> None:
        """
        构建 BM25 索引 — 对文档集进行分词并初始化 BM25Okapi

        复杂度：O(n)，其中 n 为文档总数

        Args:
            documents: 待索引的文档列表，每项为一段中文文本
        """
        # 步骤 1：保存原始文档（检索时需要返回原始文本）
        self.documents = documents

        # 步骤 2：对每篇文档执行中文分词
        # BM25Okapi 的输入是分词后的 token 列表，每个文档对应一个 token 列表
        self.tokenized_corpus = [self._tokenize(doc) for doc in documents]

        # 步骤 3：用分词后的语料实例化 BM25Okapi 索引
        # BM25Okapi 内部会计算：文档频率（DF）、平均文档长度、每篇文档的 token 频次
        self.bm25 = BM25Okapi(self.tokenized_corpus)

        # 步骤 4：标记索引已完成
        self._is_indexed = True

        print(f"[BM25] 索引构建完成，共 {len(documents)} 篇文档")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        使用 BM25 检索与查询最相关的 top_k 篇文档

        Args:
            query: 查询文本（中文）
            top_k: 返回的文档数量，默认 5

        Returns:
            检索结果列表，每项包含：
                - "rank": BM25 排名（1-based）
                - "score": BM25 相关性分数（越高越相关）
                - "document": 原始文档文本
                - "method": 固定值 "bm25"
        """
        if not self._is_indexed:
            raise RuntimeError("BM25 索引尚未构建，请先调用 index() 方法")

        # 步骤 1：对查询进行分词
        tokenized_query: List[str] = self._tokenize(query)

        # 步骤 2：使用 BM25Okapi.get_scores() 计算查询与所有文档的相关性分数
        # get_scores 返回长度为 N 的数组，scores[i] 表示查询与第 i 篇文档的 BM25 分数
        raw_scores: List[float] = self.bm25.get_scores(tokenized_query).tolist()

        # 步骤 3：按分数降序排序，取前 top_k 个
        # enumerate 生成 (index, score) 对，sorted 按 score 降序排列
        sorted_indices: List[Tuple[int, float]] = sorted(
            enumerate(raw_scores),
            key=lambda x: x[1],  # 按分数排序
            reverse=True  # 降序，分数高的在前
        )

        # 步骤 4：构建结果列表
        results: List[Dict[str, Any]] = []
        for rank, (doc_idx, score) in enumerate(sorted_indices[:top_k], start=1):
            results.append({
                "rank": rank,  # BM25 排名，从 1 开始
                "score": round(float(score), 4),  # BM25 分数，保留 4 位小数
                "document": self.documents[doc_idx],  # 原始文档文本
                "method": "bm25",  # 检索方法标识
            })

        return results


# ==================== 向量检索器 ====================

class VectorRetriever:
    """
    向量检索器 — 基于语义相似度的稠密向量检索

    核心原理：
    1. 用 Embedding 模型将文档和查询都编码为固定维度的向量（如 768 维）
    2. 在向量空间中，语义相似的文本距离更近
    3. 使用余弦相似度（cosine similarity）度量向量间的相似程度

    优点：理解语义（"苹果"和"iPhone"在语义上相关）、对同义词鲁棒
    缺点：需要 GPU 加速、可能忽略精确关键词匹配
    """

    def __init__(self, collection_name: str = "hybrid_demo") -> None:
        """
        初始化向量检索器

        Args:
            collection_name: ChromaDB 集合名称，用于隔离不同的检索实验
        """
        # 保存集合名称
        self.collection_name: str = collection_name

        # 加载 Embedding 模型（使用 HuggingFace 模型，通过镜像下载）
        # BGE-small-zh 是 BAAI 针对中文优化的轻量嵌入模型，768 维输出
        print(f"[Vector] 正在加载 Embedding 模型: BAAI/bge-small-zh-v1.5 ...")
        self.embedding_model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
        print(f"[Vector] Embedding 模型加载完成")

        # 初始化 ChromaDB 客户端（持久化模式）
        # persist_directory 指定向量数据的持久化存储路径
        persist_dir: str = str(Path(__file__).parent / "chroma_db" / collection_name)
        self.chroma_client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False  # 关闭遥测，保护隐私
            )
        )

        # 获取或创建 ChromaDB 集合
        # metadata 传入 "hnsw:space": "cosine" 指定使用余弦距离
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # 使用余弦相似度（最常用的向量相似度度量）
        )

        # 原始文档列表（从 ChromaDB 检索到向量后需要映射回原始文本）
        self.documents: List[str] = []

        # 标记是否已完成索引构建
        self._is_indexed: bool = False

    def index(self, documents: List[str], ids: Optional[List[str]] = None) -> None:
        """
        将文档集编码为向量并存入 ChromaDB

        流程：
        1. 用 embedding_model 将每篇文档编码为 768 维向量
        2. 将向量和元数据写入 ChromaDB 集合

        Args:
            documents: 待索引的文档列表
            ids: 文档 ID 列表（可选），不提供则自动生成 "doc_0", "doc_1"...
        """
        # 步骤 1：保存原始文档
        self.documents = documents

        # 步骤 2：生成文档 ID（如果没有提供）
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]

        # 步骤 3：使用 Embedding 模型批量编码文档为向量
        # encode() 返回 shape=(N, 768) 的 numpy 数组
        # show_progress_bar=True 显示编码进度
        print(f"[Vector] 正在为 {len(documents)} 篇文档生成向量嵌入...")
        embeddings = self.embedding_model.encode(
            documents,
            show_progress_bar=True,  # 显示进度条
            normalize_embeddings=True  # 归一化向量，使余弦相似度计算等价于点积
        )

        # 步骤 4：将向量和元数据添加到 ChromaDB 集合中
        # 每篇文档的元数据包含原始文本，用于检索结果展示
        self.collection.add(
            ids=ids,  # 文档唯一标识符
            embeddings=embeddings.tolist(),  # 向量列表（转换为 Python list）
            metadatas=[{"text": doc} for doc in documents]  # 元数据：存储原始文本
        )

        self._is_indexed = True
        print(f"[Vector] 向量索引构建完成，共 {len(documents)} 篇文档，向量维度 {embeddings.shape[1]}")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        使用向量相似度检索与查询最相关的 top_k 篇文档

        流程：
        1. 将查询文本编码为向量
        2. 在 ChromaDB 中执行近似最近邻（ANN）搜索
        3. 返回相似度最高的 top_k 篇文档

        Args:
            query: 查询文本（中文）
            top_k: 返回的文档数量，默认 5

        Returns:
            检索结果列表，每项包含：
                - "rank": 向量相似度排名（1-based）
                - "score": 相似度分数（余弦相似度，值域 [0, 2]，越高越相似）
                - "document": 原始文档文本
                - "method": 固定值 "vector"
        """
        if not self._is_indexed:
            raise RuntimeError("向量索引尚未构建，请先调用 index() 方法")

        # 步骤 1：将查询编码为向量
        query_embedding = self.embedding_model.encode(
            [query],
            normalize_embeddings=True  # 归一化，保证余弦相似度计算正确
        )

        # 步骤 2：在 ChromaDB 中执行 ANN 检索
        # query_embeddings 传入查询向量，n_results 指定返回数量
        raw_result = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=top_k
        )

        # 步骤 3：解析 ChromaDB 返回的结果并构建统一格式
        results: List[Dict[str, Any]] = []
        # raw_result 结构：
        #   ids[0] -> 文档 ID 列表
        #   distances[0] -> 距离列表（cosine 空间下值域 [0, 2]，越小越相似）
        #   metadatas[0] -> 元数据列表
        result_ids: List[str] = raw_result["ids"][0]  # 第一个查询的结果
        result_distances: List[float] = raw_result["distances"][0]  # 距离值
        result_metadatas: List[dict] = raw_result["metadatas"][0]  # 元数据

        for rank, (doc_id, distance, metadata) in enumerate(
            zip(result_ids, result_distances, result_metadatas), start=1
        ):
            # 余弦距离转余弦相似度：similarity = 2 - distance
            # 当使用归一化向量时，余弦距离 = 1 - cosine_similarity，距离 0 表示完全相同
            # ChromaDB 在 cosine 空间下返回的距离值是归一化后的结果
            similarity = round(float(2.0 - distance), 4)

            results.append({
                "rank": rank,  # 向量检索排名，从 1 开始
                "score": similarity,  # 余弦相似度
                "document": metadata.get("text", ""),  # 从元数据恢复原始文本
                "method": "vector",  # 检索方法标识
            })

        return results


# ==================== 混合检索器（核心） ====================

class HybridRetriever:
    """
    混合检索器 — BM25 稀疏检索 + 向量稠密检索 + RRF 融合

    核心思想：
    1. 同时运行 BM25（关键词）和向量检索（语义），各自返回 top_k 结果
    2. 用 RRF（倒数排名融合）算法合并两个排序结果
    3. RRF 公式：score(d) = sum_{i} 1 / (k + rank_i(d))
       其中 k=60 是平滑参数，rank_i(d) 是文档 d 在检索器 i 中的排名
    4. RRF 的直觉：如果一个文档在多个检索器中都排在前面，
       它的 RRF 总分就会很高，最终排名就会靠前

    RRF 的优点：
    - 无需训练，开箱即用
    - 对不同检索器的分数尺度不敏感（只关心排名，不关心绝对分数）
    - 在实践中效果稳定可靠
    """

    def __init__(self) -> None:
        """
        初始化混合检索器 — 内部组合 BM25Retriever 和 VectorRetriever
        """
        # BM25 稀疏检索器 — 负责关键词精准匹配
        self.bm25_retriever: BM25Retriever = BM25Retriever()

        # 向量检索器 — 负责语义相似度匹配
        self.vector_retriever: VectorRetriever = VectorRetriever()

        # 记录是否已完成索引
        self._is_indexed: bool = False

    def index(self, documents: List[str]) -> None:
        """
        同时构建 BM25 索引和向量索引

        Args:
            documents: 待索引的文档列表
        """
        # 分别调用两个检索器的 index 方法
        print("[Hybrid] 开始构建混合索引...")
        print("[Hybrid] Step 1/2: 构建 BM25 索引...")
        self.bm25_retriever.index(documents)

        print("[Hybrid] Step 2/2: 构建向量索引...")
        self.vector_retriever.index(documents)

        self._is_indexed = True
        print("[Hybrid] 混合索引构建完成！")

    def _rrf_fusion(
        self,
        bm25_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        k: int = RRF_K
    ) -> List[Dict[str, Any]]:
        """
        RRF（Reciprocal Rank Fusion）倒数排名融合算法

        公式：RRF_score(d) = \sum_{i} \frac{1}{k + rank_i(d)}

        Args:
            bm25_results: BM25 检索结果列表
            vector_results: 向量检索结果列表
            k: 平滑参数（默认 60），防止排名为 1 的文档分数过高
               - k 越大，排名差异的影响越小（分数越平均）
               - k 越小，排名差异的影响越大（高分文档优势更大）
               - 业界经验值 k=60 在大多数场景下工作良好

        Returns:
            RRF 融合后的排序结果列表
        """
        # 步骤 1：用字典存储每个文档（通过文本内容去重识别）的 RRF 累积分和排名信息
        rrf_scores: Dict[str, float] = {}  # doc_text -> 累积 RRF 分数
        rank_info: Dict[str, Dict[str, int]] = {}  # doc_text -> {"bm25": rank, "vector": rank}

        # 步骤 2：累加 BM25 各文档的 RRF 贡献
        for item in bm25_results:
            doc_text: str = item["document"]  # 用文档文本作为唯一标识
            doc_rank: int = item["rank"]  # BM25 中的排名（1-based）

            # RRF 公式：1 / (k + rank)
            rrf_scores[doc_text] = rrf_scores.get(doc_text, 0.0) + (1.0 / (k + doc_rank))

            # 记录排名信息（用于后续展示）
            if doc_text not in rank_info:
                rank_info[doc_text] = {}
            rank_info[doc_text]["bm25"] = doc_rank

        # 步骤 3：累加向量检索各文档的 RRF 贡献
        for item in vector_results:
            doc_text: str = item["document"]
            doc_rank: int = item["rank"]

            # 同一文档的 RRF 分数继续累加（即使 BM25 中没出现也直接累加）
            rrf_scores[doc_text] = rrf_scores.get(doc_text, 0.0) + (1.0 / (k + doc_rank))

            if doc_text not in rank_info:
                rank_info[doc_text] = {}
            rank_info[doc_text]["vector"] = doc_rank

        # 步骤 4：按 RRF 总分降序排序
        sorted_docs: List[Tuple[str, float]] = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],  # 按 RRF 分数排序
            reverse=True  # 降序：分数高的在前
        )

        # 步骤 5：构建统一格式的结果列表
        results: List[Dict[str, Any]] = []
        for rank, (doc_text, rrf_score) in enumerate(sorted_docs, start=1):
            info: Dict[str, int] = rank_info.get(doc_text, {})
            bm25_rank: Optional[int] = info.get("bm25")  # BM25 中的排名（可能为 None）
            vector_rank: Optional[int] = info.get("vector")  # 向量检索中的排名（可能为 None）

            results.append({
                "rank": rank,  # RRF 融合后的最终排名
                "rrf_score": round(rrf_score, 4),  # RRF 融合分数
                "bm25_rank": bm25_rank,  # 该文档在 BM25 中的排名
                "vector_rank": vector_rank,  # 该文档在向量检索中的排名
                "document": doc_text,  # 原始文档文本
                "method": "hybrid_rrf",  # 检索方法标识
            })

        return results

    def search(
        self,
        query: str,
        top_k: int = 5,
        verbose: bool = True
    ) -> List[Dict[str, Any]]:
        """
        混合检索 — 分别执行 BM25 和向量检索，然后 RRF 融合

        流程图：
        ┌─────────────┐
        │   查询文本   │
        └─────┬───────┘
              │
        ┌─────┴───────┐
        │             │
        ▼             ▼
        ┌───────┐  ┌────────┐
        │ BM25  │  │ Vector │
        │ 检索  │  │  检索   │
        └───┬───┘  └───┬────┘
            │          │
            ▼          ▼
        ┌───────────────────┐
        │   RRF 融合排序    │
        │ score = 1/(k+rank)│
        └────────┬──────────┘
                 │
                 ▼
        ┌───────────────────┐
        │   Top-K 最终结果  │
        └───────────────────┘

        Args:
            query: 查询文本（中文）
            top_k: 最终返回的文档数量，默认 5
            verbose: 是否打印详细的检索过程，默认 True

        Returns:
            RRF 融合后的检索结果列表（前 top_k 个）
        """
        if not self._is_indexed:
            raise RuntimeError("混合索引尚未构建，请先调用 index() 方法")

        if verbose:
            print(f"\n{'='*60}")
            print(f"[Hybrid] 查询: \"{query}\"")
            print(f"{'='*60}")

        # 步骤 1：BM25 稀疏检索
        # 为了 RRF 融合的公平性，BM25 取 2*top_k 个候选（避免漏掉较好的文档）
        bm25_results: List[Dict[str, Any]] = self.bm25_retriever.search(query, top_k=top_k * 2)

        if verbose:
            print(f"\n--- BM25 检索结果（Top-{top_k}）---")
            for item in bm25_results[:top_k]:
                print(f"  排名 #{item['rank']}: 分数={item['score']:.4f} | {item['document'][:50]}...")

        # 步骤 2：向量稠密检索
        vector_results: List[Dict[str, Any]] = self.vector_retriever.search(query, top_k=top_k * 2)

        if verbose:
            print(f"\n--- 向量检索结果（Top-{top_k}）---")
            for item in vector_results[:top_k]:
                print(f"  排名 #{item['rank']}: 相似度={item['score']:.4f} | {item['document'][:50]}...")

        # 步骤 3：RRF 融合排序
        fused_results: List[Dict[str, Any]] = self._rrf_fusion(bm25_results, vector_results)

        if verbose:
            print(f"\n--- RRF 融合结果（Top-{top_k}）---")
            for item in fused_results[:top_k]:
                bm25_r = item.get("bm25_rank", "-")
                vec_r = item.get("vector_rank", "-")
                print(f"  排名 #{item['rank']}: RRF={item['rrf_score']:.4f} "
                      f"(BM25排#{bm25_r}, Vec排#{vec_r}) | {item['document'][:50]}...")

        # 步骤 4：返回前 top_k 个结果
        return fused_results[:top_k]


# ==================== 模块演示入口 ====================

def main() -> None:
    """
    混合检索模块的独立演示

    展示 BM25、向量和混合检索三种方法在相同查询下的效果差异，
    帮助理解为什么混合检索优于单一方法。
    """
    print("=" * 70)
    print("  Day 18: 混合检索演示 — BM25 + Vector + RRF 融合")
    print("=" * 70)

    # 实例化三个检索器
    bm25 = BM25Retriever()
    vector = VectorRetriever()
    hybrid = HybridRetriever()

    # 构建索引
    print("\n>>> 正在构建索引...")
    bm25.index(DEMO_DOCUMENTS)
    vector.index(DEMO_DOCUMENTS)
    hybrid.index(DEMO_DOCUMENTS)

    # 测试查询 — 覆盖不同的检索场景
    test_queries: List[str] = [
        "什么是深度学习？",  # 语义查询 — 向量检索优势场景
        "RAG 技术如何工作？",  # 混合查询 — 包含专业术语和概念
        "Python 编程语言",  # 关键词精确匹配 — BM25 优势场景
    ]

    for query in test_queries:
        # BM25 单独检索
        print(f"\n{'='*70}")
        print(f"  [BM25 Only] 查询: \"{query}\"")
        bm25_results = bm25.search(query, top_k=3)
        for item in bm25_results:
            print(f"    #{item['rank']}: {item['document'][:60]}...")

        # 向量单独检索
        print(f"\n  [Vector Only] 查询: \"{query}\"")
        vector_results = vector.search(query, top_k=3)
        for item in vector_results:
            print(f"    #{item['rank']}: {item['document'][:60]}...")

        # 混合检索（含 RRF 融合）
        print(f"\n  [Hybrid RRF] 查询: \"{query}\"")
        hybrid_results = hybrid.search(query, top_k=3, verbose=False)
        for item in hybrid_results:
            bm25_r = item.get("bm25_rank", "-")
            vec_r = item.get("vector_rank", "-")
            print(f"    #{item['rank']}: RRF={item['rrf_score']:.4f} "
                  f"(BM25#{bm25_r}, Vec#{vec_r}) | {item['document'][:60]}...")

    print(f"\n{'='*70}")
    print("  BM25 vs Vector vs Hybrid 对比总结:")
    print("  • BM25: 擅长精确关键词匹配，对拼写/同义词不敏感")
    print("  • Vector: 擅长语义理解，但可能遗漏关键术语")
    print("  • Hybrid (RRF): 取两者之长，结果更全面可靠")
    print(f"{'='*70}")


# 如果直接运行此文件，执行演示
if __name__ == "__main__":
    main()
