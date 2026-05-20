"""
production_rag.py — 生产级 RAG 系统

整合所有生产关注点：
1. 配置管理 — RAGConfig 集中管控所有参数
2. 结构化日志 — JSON 格式日志，便于 ELK/Splunk 采集
3. TTL+LRU 缓存 — 减少重复查询的 LLM 调用成本
4. 指数退避重试 — 应对 API 临时故障
5. 混合检索 — 向量检索 + BM25 关键字检索 → RRF 融合
6. Cross-Encoder 重排序 — 提升检索精度
7. 性能指标收集 — 缓存命中率、平均延迟、错误计数

架构：
  用户查询 → 缓存检查 → (miss) → 混合检索 → 重排序 → LLM 生成 → 缓存存储 → 返回
                        → (hit)  → 直接返回缓存结果

依赖：ChromaDB + sentence-transformers + openai SDK + rank-bm25
设计原则：零 LangChain，零硬编码 API Key，全部类型标注
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, HF_ENDPOINT

import os
# 必须在导入 sentence-transformers 之前设置 HF_ENDPOINT，确保模型从国内镜像下载
os.environ["HF_ENDPOINT"] = HF_ENDPOINT if HF_ENDPOINT else "https://hf-mirror.com"

import time                     # 用于缓存 TTL、重试等待、性能计时
import json                     # 用于结构化日志输出
import time as time_module      # 别名避免与局部变量冲突
import re                       # 用于 BM25 文本分词（正则分割）
from datetime import datetime   # 用于日志时间戳
from typing import List, Dict, Optional, Any, Callable  # 类型标注
from collections import OrderedDict  # 用于 LRU 缓存（保持插入顺序）

import chromadb                                 # 向量数据库
from chromadb import PersistentClient           # 持久化客户端（数据存磁盘）
from chromadb.api import Collection             # Collection 类型标注
from sentence_transformers import SentenceTransformer, CrossEncoder  # 嵌入模型 + 重排序模型
from openai import OpenAI                       # LLM API 客户端
from rank_bm25 import BM25Okapi                 # BM25 关键字检索算法

from rag_config import RAGConfig  # 本模块的配置数据类


# ==============================================================================
# 辅助组件 1：结构化 JSON 日志器
# ==============================================================================

class StructuredLogger:
    """生产级结构化日志 — JSON 格式，便于日志聚合系统（ELK/Loki）解析

    日志级别（从低到高）：DEBUG=10, INFO=20, WARNING=30, ERROR=40
    """

    # 日志级别映射 — 级别名 → 数值
    _LEVELS: Dict[str, int] = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}

    def __init__(self, level: str = "INFO", component: str = "ProductionRAG") -> None:
        self._level_value: int = self._LEVELS.get(level, 20)  # 当前级别阈值
        self._component: str = component  # 组件名称，用于日志分类

    def _log(self, level: str, message: str, **kwargs: Any) -> None:
        """内部日志方法 — 构建 JSON 条目并输出到 stdout"""
        if self._LEVELS.get(level, 0) < self._level_value:
            return  # 低于当前级别的日志不输出
        entry: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),  # ISO8601 格式时间戳
            "level": level,                           # 日志级别
            "component": self._component,             # 来源组件
            "message": message,                       # 日志消息
        }
        entry.update(kwargs)  # 合并额外的结构化字段（如 latency_ms、doc_count 等）
        # 输出单行 JSON（确保中文正常显示）
        print(json.dumps(entry, ensure_ascii=False, default=str))

    def debug(self, message: str, **kwargs: Any) -> None:
        """调试级别日志 — 开发环境详细信息"""
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """信息级别日志 — 正常运行的关键事件"""
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """警告级别日志 — 可恢复的异常情况"""
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """错误级别日志 — 需要人工介入的故障"""
        self._log("ERROR", message, **kwargs)


# ==============================================================================
# 辅助组件 2：TTL + LRU 缓存
# ==============================================================================

class TTLCache:
    """带 TTL 过期和 LRU 淘汰的本地内存缓存

    工作原理：
    - TTL（Time-To-Live）：每个缓存条目在设定时间后自动过期
    - LRU（Least Recently Used）：缓存满时淘汰最久未访问的条目
    - 使用 OrderedDict 天然支持 LRU（访问时移到末尾）
    """

    def __init__(self, max_size: int = 1000, ttl: int = 3600) -> None:
        self._max_size: int = max_size           # 最大缓存条目数
        self._ttl: int = ttl                     # 缓存生存时间（秒）
        # OrderedDict: key → (value, timestamp)，按插入顺序排列
        self._store: OrderedDict = OrderedDict()
        # 统计计数器
        self.hits: int = 0                       # 缓存命中次数
        self.misses: int = 0                     # 缓存未命中次数

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值 — 命中则返回，过期则删除，未命中返回 None"""
        if key not in self._store:
            self.misses += 1
            return None

        value, timestamp = self._store[key]

        # 检查 TTL 是否过期
        if time.time() - timestamp > self._ttl:
            del self._store[key]  # 删除过期条目
            self.misses += 1
            return None

        # LRU 更新：将访问的条目移到末尾（代表最近使用）
        self._store.move_to_end(key)
        self.hits += 1
        return value

    def set(self, key: str, value: Any) -> None:
        """存入缓存 — 满时淘汰最久未访问的条目（LRU 淘汰）"""
        if key in self._store:
            del self._store[key]  # 更新已存在的键（刷新位置）
        elif len(self._store) >= self._max_size:
            # FIFO 淘汰：弹出第一个（最久未访问的）条目
            oldest_key, _ = self._store.popitem(last=False)
        self._store[key] = (value, time.time())  # 存储值 + 时间戳

    def clear(self) -> None:
        """清空所有缓存条目"""
        self._store.clear()
        self.hits = 0
        self.misses = 0

    @property
    def size(self) -> int:
        """当前缓存条目数"""
        return len(self._store)


# ==============================================================================
# 辅助组件 3：性能指标收集器
# ==============================================================================

class MetricsTracker:
    """请求级性能指标收集器 — 追踪查询延迟、缓存命中率、错误数"""

    def __init__(self) -> None:
        self.total_queries: int = 0      # 总查询次数
        self.cache_hits: int = 0         # 缓存命中次数
        self.cache_misses: int = 0       # 缓存未命中次数
        self.total_retrieval_ms: float = 0.0   # 检索阶段累计耗时（毫秒）
        self.total_generation_ms: float = 0.0  # 生成阶段累计耗时（毫秒）
        self.total_rerank_ms: float = 0.0      # 重排序阶段累计耗时（毫秒）
        self.error_count: int = 0              # 查询失败次数
        self._query_latencies: List[float] = []  # 最近查询的端到端延迟列表

    def record_query(
        self,
        cache_hit: bool,
        retrieval_ms: float,
        generation_ms: float,
        rerank_ms: float,
        total_ms: float,
        success: bool = True,
    ) -> None:
        """记录一次查询的完整指标"""
        self.total_queries += 1
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        self.total_retrieval_ms += retrieval_ms
        self.total_generation_ms += generation_ms
        self.total_rerank_ms += rerank_ms
        if not success:
            self.error_count += 1
        self._query_latencies.append(total_ms)
        # 只保留最近 100 次查询的延迟记录
        if len(self._query_latencies) > 100:
            self._query_latencies.pop(0)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计摘要 — 平均延迟、命中率、错误率"""
        n = max(self.total_queries, 1)  # 防止除零
        return {
            "total_queries": self.total_queries,     # 总查询数
            "cache_hits": self.cache_hits,           # 缓存命中数
            "cache_misses": self.cache_misses,       # 缓存未命中数
            "cache_hit_rate": round(self.cache_hits / n, 4),  # 缓存命中率（0-1）
            "avg_retrieval_ms": round(self.total_retrieval_ms / n, 2),  # 平均检索延迟
            "avg_generation_ms": round(self.total_generation_ms / n, 2),  # 平均生成延迟
            "avg_rerank_ms": round(self.total_rerank_ms / n, 2),  # 平均重排序延迟
            "error_count": self.error_count,         # 错误总数
            "error_rate": round(self.error_count / n, 4),  # 错误率
            "p50_latency_ms": self._percentile(50),  # 中位数延迟
            "p95_latency_ms": self._percentile(95),  # 95 分位延迟
        }

    def _percentile(self, p: float) -> float:
        """计算指定百分位的端到端延迟"""
        if not self._query_latencies:
            return 0.0
        sorted_latencies = sorted(self._query_latencies)
        idx = int(len(sorted_latencies) * p / 100)
        idx = min(idx, len(sorted_latencies) - 1)
        return round(sorted_latencies[idx], 2)


# ==============================================================================
# 辅助组件 4：ChromaDB 自定义嵌入函数
# ==============================================================================

class CustomEmbeddingFunction:
    """自定义嵌入函数 — 封装 SentenceTransformer 供 ChromaDB 调用

    ChromaDB 要求嵌入函数实现 __call__(texts) → List[List[float]]
    """

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5") -> None:
        self._model: SentenceTransformer = SentenceTransformer(model_name)

    def __call__(self, texts: List[str]) -> List[List[float]]:
        """将文本列表转换为向量列表 — ChromaDB 调用入口"""
        return self._model.encode(texts, show_progress_bar=False).tolist()


# ==============================================================================
# 主类：生产级 RAG 系统
# ==============================================================================

class ProductionRAG:
    """生产级 RAG 系统 — 整合配置、日志、缓存、指标、混合检索、重排序

    查询管道（完整路径）：
        缓存检查 → 混合检索(BM25+向量→RRF) → 重排序(Cross-Encoder)
        → LLM 生成 → 缓存存储 → 记录指标 → 返回结果

    使用示例：
        config = RAGConfig()
        rag = ProductionRAG(config)
        rag.index_documents(["文档1内容...", "文档2内容..."])
        result = rag.query("什么是 RAG?")
    """

    def __init__(self, config: Optional[RAGConfig] = None) -> None:
        # ---- 配置 ----
        self.config: RAGConfig = config if config is not None else RAGConfig()

        # ---- 日志器 ----
        self._logger: StructuredLogger = StructuredLogger(
            level=self.config.log_level, component="ProductionRAG"
        )
        self._logger.info("初始化生产级RAG系统", config=self.config.to_dict())

        # ---- 缓存 ----
        self._cache: TTLCache = TTLCache(
            max_size=self.config.cache_max_size, ttl=self.config.cache_ttl
        )

        # ---- 指标 ----
        self._metrics: MetricsTracker = MetricsTracker()

        # ---- 嵌入函数 ----
        self._embed_fn: CustomEmbeddingFunction = CustomEmbeddingFunction(
            model_name=self.config.embedding_model
        )

        # ---- ChromaDB 向量库 ----
        self._init_chromadb()

        # ---- BM25 索引（懒加载） ----
        self._documents: List[str] = []   # 存储文档原始文本（用于 BM25 构建）
        self._bm25: Optional[BM25Okapi] = None  # BM25 索引对象

        # ---- 重排序器（懒加载） ----
        self._reranker: Optional[CrossEncoder] = None

        # ---- LLM 客户端 ----
        self._llm: OpenAI = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

        self._logger.info("生产级RAG系统初始化完成", collection=self.config.collection_name)

    # ---- 初始化辅助方法 ----

    def _init_chromadb(self) -> None:
        """初始化 ChromaDB 向量数据库客户端和 Collection"""
        # 确定持久化路径（默认存储在模块同级的 chroma_data 目录）
        db_path: str = self.config.db_path or str(Path(__file__).parent / "chroma_data")
        self._client: PersistentClient = chromadb.PersistentClient(path=db_path)
        # 获取或创建 Collection（嵌入函数随 Collection 绑定）
        self._collection: Collection = self._client.get_or_create_collection(
            name=self.config.collection_name,
            embedding_function=self._embed_fn,
        )
        self._logger.info(
            "ChromaDB初始化完成",
            db_path=db_path,
            collection=self.config.collection_name,
            doc_count=self._collection.count(),
        )

    def _build_bm25(self) -> None:
        """从已存储文档构建（或重建）BM25 关键字检索索引"""
        if not self._documents:
            self._bm25 = None
            self._logger.info("BM25索引为空（无文档）")
            return
        # 对每篇文档进行分词（中文按字符+标点分割）
        tokenized: List[List[str]] = [self._tokenize(doc) for doc in self._documents]
        self._bm25 = BM25Okapi(tokenized)  # 构建 BM25 索引
        self._logger.info("BM25索引构建完成", doc_count=len(self._documents))

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """中文文本分词 — 按字符级 + 英文/数字保持连续

        使用正则：匹配中文字符单独切分，英文/数字保持单词完整性
        这是 BM25 的基础分词策略，适合中英混合文档
        """
        # 正则：匹配连续英文字母/数字，或单个中文字符
        tokens: List[str] = re.findall(r"[a-zA-Z0-9]+|[一-鿿]|[^\s]", text)
        return tokens

    # ---- 公开接口：索引 ----

    def index_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> int:
        """索引阶段：将文档列表存入 ChromaDB 并构建 BM25 索引

        Args:
            documents: 待索引的文档文本列表（已分块）
            metadatas: 每条文档对应的元数据列表（可选）
            ids: 文档唯一 ID 列表（可选，默认自动生成）

        Returns:
            int: 新索引的文档数量
        """
        if not documents:
            self._logger.warning("索引文档列表为空，跳过")
            return 0

        # 自动生成 ID（基于 Collection 当前总数）
        if ids is None:
            start_idx: int = self._collection.count()
            ids = [f"doc_{start_idx + i}" for i in range(len(documents))]

        # 步骤 1：存入 ChromaDB（自动嵌入 + 持久化）
        start_time: float = time.time()
        self._collection.add(documents=documents, metadatas=metadatas, ids=ids)
        chroma_ms: float = (time.time() - start_time) * 1000

        # 步骤 2：追加到本地文档列表（供 BM25 使用）
        self._documents.extend(documents)

        # 步骤 3：重建 BM25 索引
        start_time = time.time()
        self._build_bm25()
        bm25_ms: float = (time.time() - start_time) * 1000

        self._logger.info(
            "文档索引完成",
            new_count=len(documents),
            total_count=self._collection.count(),
            chromadb_ms=round(chroma_ms, 2),
            bm25_ms=round(bm25_ms, 2),
        )
        return len(documents)

    # ---- 公开接口：查询 ----

    def query(self, query: str, use_cache: bool = True) -> Dict[str, Any]:
        """完整 RAG 查询管道 — 生产级实现

        管道步骤：
        1. 缓存检查（命中则跳过检索和生成）
        2. 混合检索（BM25 + 向量 → RRF 融合）
        3. Cross-Encoder 重排序
        4. LLM 基于检索结果生成答案
        5. 更新缓存和指标

        Args:
            query: 用户查询文本
            use_cache: 是否使用缓存（默认 True）

        Returns:
            dict: {"query", "answer", "sources", "cached", "timing"}
        """
        query_start: float = time.time()
        cache_hit: bool = False
        success: bool = True
        retrieval_ms: float = 0.0
        rerank_ms: float = 0.0
        generation_ms: float = 0.0

        self._logger.info("开始查询", query=query, use_cache=use_cache)

        # ---- 步骤 1：缓存查询 ----
        if use_cache:
            cached: Optional[Dict[str, Any]] = self._cache.get(query)
            if cached is not None:
                elapsed: float = (time.time() - query_start) * 1000
                self._metrics.record_query(
                    cache_hit=True, retrieval_ms=0, generation_ms=0,
                    rerank_ms=0, total_ms=elapsed, success=True,
                )
                self._logger.info("缓存命中", query=query, latency_ms=round(elapsed, 2))
                return {**cached, "cached": True, "timing": {"total_ms": round(elapsed, 2)}}
        cache_hit = False  # 未命中缓存

        try:
            # ---- 步骤 2：检索阶段 ----
            retrieval_start: float = time.time()
            docs: List[Dict[str, Any]] = self._retrieve(query)  # 混合/向量检索
            retrieval_ms = (time.time() - retrieval_start) * 1000
            self._logger.info(
                "检索完成", query=query, doc_count=len(docs),
                latency_ms=round(retrieval_ms, 2),
            )

            # ---- 步骤 3：重排序阶段 ----
            if self.config.use_reranker and len(docs) > 1:
                rerank_start: float = time.time()
                docs = self._rerank(query, docs)
                rerank_ms = (time.time() - rerank_start) * 1000
                self._logger.info(
                    "重排序完成", query=query, doc_count=len(docs),
                    latency_ms=round(rerank_ms, 2),
                )

            # ---- 步骤 4：生成阶段 ----
            gen_start: float = time.time()
            answer: str = self._generate(query, docs)
            generation_ms = (time.time() - gen_start) * 1000
            self._logger.info(
                "生成完成", query=query, answer_len=len(answer),
                latency_ms=round(generation_ms, 2),
            )

        except Exception as e:
            success = False
            total_ms: float = (time.time() - query_start) * 1000
            self._metrics.record_query(
                cache_hit=False, retrieval_ms=retrieval_ms,
                generation_ms=generation_ms, rerank_ms=rerank_ms,
                total_ms=total_ms, success=False,
            )
            self._logger.error("查询失败", query=query, error=str(e))
            raise

        # ---- 步骤 5：构建结果 ----
        total_ms = (time.time() - query_start) * 1000
        result: Dict[str, Any] = {
            "query": query,
            "answer": answer,
            "sources": [
                {"content": d["content"][:200], "score": round(d.get("score", 0), 4)}
                for d in docs[:3]  # 只返回 Top-3 来源
            ],
            "cached": False,
            "timing": {
                "total_ms": round(total_ms, 2),
                "retrieval_ms": round(retrieval_ms, 2),
                "rerank_ms": round(rerank_ms, 2),
                "generation_ms": round(generation_ms, 2),
            },
        }

        # ---- 步骤 6：更新缓存和指标 ----
        if use_cache:
            self._cache.set(query, {"query": query, "answer": answer, "sources": result["sources"]})
        self._metrics.record_query(
            cache_hit=False, retrieval_ms=retrieval_ms,
            generation_ms=generation_ms, rerank_ms=rerank_ms,
            total_ms=total_ms, success=True,
        )

        self._logger.info(
            "查询完成", query=query, total_ms=round(total_ms, 2),
            cache_hit=cache_hit, doc_count=len(docs),
        )
        return result

    # ---- 检索方法 ----

    def _retrieve(self, query: str) -> List[Dict[str, Any]]:
        """检索分发 — 根据配置选择混合检索或纯向量检索"""
        if self.config.use_hybrid and self._bm25 is not None:
            return self._hybrid_retrieve(query)
        else:
            return self._vector_retrieve(query)

    def _vector_retrieve(self, query: str) -> List[Dict[str, Any]]:
        """纯向量语义检索 — 从 ChromaDB 按余弦距离搜索 Top-K"""
        if self._collection.count() == 0:
            return []

        results = self._collection.query(
            query_texts=[query],
            n_results=min(self.config.top_k * 2, self._collection.count()),
        )
        docs: List[Dict[str, Any]] = []
        for idx, (doc, distance) in enumerate(
            zip(results["documents"][0], results["distances"][0])
        ):
            docs.append({
                "content": doc,
                "score": round(1.0 - distance, 4),  # 距离转相似度分数
                "rank": idx + 1,
                "source": "vector",  # 标记来源
            })
        return docs

    def _hybrid_retrieve(self, query: str) -> List[Dict[str, Any]]:
        """混合检索 — 向量语义检索 + BM25 关键字检索 → RRF 融合

        RRF（Reciprocal Rank Fusion）：
            RRF_score(d) = Σ 1/(k + rank_i(d))
            其中 k=60，rank_i(d) 是在检索方法 i 中的排名

        优势：向量理解语义 + BM25 精确匹配关键词，互补增强
        """
        # ---- 并行获取两路检索结果 ----
        vector_docs: List[Dict[str, Any]] = self._vector_retrieve(query)
        bm25_docs: List[Dict[str, Any]] = self._bm25_retrieve(query)

        # ---- RRF 融合 ----
        fused: Dict[str, Dict[str, Any]] = {}  # content_hash → {content, rrf_score}
        k: int = 60  # RRF 平滑常数（标准值）

        # 向量检索结果计入 RRF
        for rank, doc in enumerate(vector_docs):
            content_key: str = doc["content"][:100]  # 用前100字符作为近似键
            rrf_score: float = 1.0 / (k + rank + 1)  # rank 从 0 开始，转为 1-based
            if content_key in fused:
                fused[content_key]["rrf_score"] += rrf_score
            else:
                fused[content_key] = {"content": doc["content"], "rrf_score": rrf_score}

        # BM25 检索结果计入 RRF
        for rank, doc in enumerate(bm25_docs):
            content_key = doc["content"][:100]
            rrf_score = 1.0 / (k + rank + 1)
            if content_key in fused:
                fused[content_key]["rrf_score"] += rrf_score
            else:
                fused[content_key] = {"content": doc["content"], "rrf_score": rrf_score}

        # 按 RRF 分数降序排序、取 Top-K
        ranked: List[Dict[str, Any]] = sorted(
            fused.values(), key=lambda x: x["rrf_score"], reverse=True
        )
        top_results: List[Dict[str, Any]] = ranked[: self.config.top_k]

        # 补充 rank 信息
        for i, doc in enumerate(top_results):
            doc["rank"] = i + 1
            doc["score"] = round(doc["rrf_score"], 6)
            doc["source"] = "hybrid_rrf"

        self._logger.info(
            "RRF融合完成",
            vector_count=len(vector_docs),
            bm25_count=len(bm25_docs),
            fused_count=len(top_results),
        )
        return top_results

    def _bm25_retrieve(self, query: str) -> List[Dict[str, Any]]:
        """BM25 关键字检索 — 基于词频-逆文档频率的经典检索算法"""
        if self._bm25 is None or not self._documents:
            return []

        # 对查询进行同样分词
        tokenized_query: List[str] = self._tokenize(query)
        # 获取 BM25 分数（对每篇文档的打分）
        scores: Any = self._bm25.get_scores(tokenized_query)
        # 按分数降序排列，取 Top-K * 2
        top_indices: Any = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[: self.config.top_k * 2]

        docs: List[Dict[str, Any]] = []
        for rank, idx in enumerate(top_indices):
            if scores[idx] > 0:  # 过滤掉完全不相关的文档
                docs.append({
                    "content": self._documents[idx],
                    "score": round(float(scores[idx]), 4),
                    "rank": rank + 1,
                    "source": "bm25",
                })
        return docs

    # ---- 重排序 ----

    def _rerank(self, query: str, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Cross-Encoder 重排序 — 用精排模型对候选文档重新打分

        Cross-Encoder 同时接收 query 和 document，计算深度语义相关性，
        精度远高于双塔模型（Bi-Encoder），但速度较慢，适合对 Top-K 候选重排
        """
        # 懒加载重排序模型（首次使用时初始化）
        if self._reranker is None:
            self._logger.info("加载重排序模型", model=self.config.reranker_model)
            self._reranker = CrossEncoder(self.config.reranker_model)

        # 构建 (query, document) 配对
        pairs: List[List[str]] = [[query, doc["content"]] for doc in docs]
        # Cross-Encoder 批量打分
        scores: Any = self._reranker.predict(pairs, show_progress_bar=False)

        # 将分数合并到文档列表
        for doc, score in zip(docs, scores):
            doc["rerank_score"] = round(float(score), 4)

        # 按重排序分数降序排列
        docs.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

        # 更新 rank 和最终 score
        for i, doc in enumerate(docs):
            doc["rank"] = i + 1
            doc["score"] = doc["rerank_score"]  # 最终分数 = 重排序分数

        return docs[: self.config.top_k]

    # ---- LLM 生成 ----

    def _generate(self, query: str, docs: List[Dict[str, Any]]) -> str:
        """基于检索文档生成答案 — 带指数退避重试

        将检索到的文档注入 prompt 作为上下文，约束 LLM 基于给定资料回答
        """
        # 构建上下文文本
        context_text: str = "\n\n---\n".join([
            f"[参考文档 {d.get('rank', i+1)}] (相关度: {d.get('score', 0):.4f})\n{d['content']}"
            for i, d in enumerate(docs)
        ])

        # 系统提示词
        system_prompt: str = (
            "你是一个基于知识库的问答助手。请严格仅根据提供的参考文档内容回答问题。\n"
            "规则：\n"
            "1. 如果文档中有明确答案，请准确引用并注明文档编号\n"
            "2. 如果文档中信息不足以回答问题，请明确说'现有资料中未找到相关信息'\n"
            "3. 不要编造文档中没有的信息\n"
            "4. 回答应简洁、准确、有引用来源"
        )

        # 定义生成函数（供重试装饰器调用）
        def _call_llm() -> str:
            response = self._llm.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"参考文档：\n{context_text}\n\n用户问题：{query}",
                    },
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.request_timeout,
            )
            content: Optional[str] = response.choices[0].message.content
            return content if content else "模型未返回有效答案"

        # 指数退避重试
        return self._retry_with_backoff(_call_llm, operation=f"LLM生成: {query[:50]}")

    # ---- 重试机制 ----

    def _retry_with_backoff(self, func: Callable[[], Any], operation: str = "") -> Any:
        """指数退避重试 — 应对 API 临时故障（限流、网络抖动）

        重试策略：
        - 第 1 次重试等待 retry_delay 秒
        - 第 2 次重试等待 retry_delay * 2 秒
        - 第 3 次重试等待 retry_delay * 4 秒
        - ...
        - 超过 max_retries 次后抛出最后一次的异常
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):  # 共 max_retries+1 次尝试
            try:
                if attempt > 0:
                    self._logger.info(
                        f"重试第{attempt}次", operation=operation
                    )
                return func()
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries:
                    # 计算本次等待时间（指数增长）
                    wait_seconds: float = self.config.retry_delay * (2 ** attempt)
                    self._logger.warning(
                        "调用失败，准备重试",
                        operation=operation,
                        attempt=attempt + 1,
                        wait_seconds=wait_seconds,
                        error=str(e),
                    )
                    time.sleep(wait_seconds)

        # 所有重试都用尽
        self._logger.error(
            "所有重试均失败", operation=operation, max_retries=self.config.max_retries
        )
        raise last_error  # type: ignore[misc]

    # ---- 指标与健康检查 ----

    def get_stats(self) -> Dict[str, Any]:
        """获取系统运行统计 — 包含查询指标和缓存信息"""
        metrics: Dict[str, Any] = self._metrics.get_stats()
        # 补充缓存维度的信息
        metrics["cache_size"] = self._cache.size
        metrics["cache_hits_detail"] = self._cache.hits
        metrics["cache_misses_detail"] = self._cache.misses
        return metrics

    def health_check(self) -> Dict[str, Any]:
        """系统健康检查 — 验证所有组件是否正常

        检查项：
        1. ChromaDB 连接状态
        2. LLM API 连通性
        3. 嵌入模型是否加载
        4. 文档数量
        5. BM25 索引状态
        6. 重排序模型状态
        """
        checks: Dict[str, Any] = {}

        # 检查 1：ChromaDB 连接
        try:
            _ = self._collection.count()
            checks["chromadb"] = {"status": "ok", "doc_count": self._collection.count()}
        except Exception as e:
            checks["chromadb"] = {"status": "error", "error": str(e)}

        # 检查 2：嵌入模型
        try:
            test_emb = self._embed_fn(["健康检查测试文本"])
            checks["embedding_model"] = {
                "status": "ok",
                "model": self.config.embedding_model,
                "dim": len(test_emb[0]),
            }
        except Exception as e:
            checks["embedding_model"] = {"status": "error", "error": str(e)}

        # 检查 3：LLM API 连通性（轻量级测试调用）
        try:
            response = self._llm.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
                timeout=10,
            )
            checks["llm_api"] = {
                "status": "ok",
                "model": OPENAI_MODEL,
                "response": response.choices[0].message.content,
            }
        except Exception as e:
            checks["llm_api"] = {"status": "error", "error": str(e)}

        # 检查 4：BM25 索引
        checks["bm25"] = {
            "status": "ok" if self._bm25 is not None else "empty",
            "doc_count": len(self._documents),
        }

        # 检查 5：重排序模型
        if self.config.use_reranker:
            checks["reranker"] = {
                "status": "loaded" if self._reranker is not None else "not_loaded",
                "model": self.config.reranker_model,
            }
        else:
            checks["reranker"] = {"status": "disabled"}

        # 检查 6：缓存状态
        checks["cache"] = {
            "size": self._cache.size,
            "max_size": self.config.cache_max_size,
            "ttl_seconds": self.config.cache_ttl,
        }

        # 汇总健康状态
        has_error: bool = any(
            v.get("status") == "error" for v in checks.values()
            if isinstance(v, dict)
        )
        checks["overall"] = "unhealthy" if has_error else "healthy"

        self._logger.info("健康检查完成", overall=checks["overall"])
        return checks

    def reset(self) -> None:
        """重置系统 — 清空向量库、缓存、指标和 BM25 索引"""
        # 删除 ChromaDB Collection
        try:
            self._client.delete_collection(self.config.collection_name)
        except Exception:
            pass
        # 重新创建空 Collection
        self._collection = self._client.get_or_create_collection(
            name=self.config.collection_name,
            embedding_function=self._embed_fn,
        )
        # 清空内存状态
        self._documents.clear()
        self._bm25 = None
        self._cache.clear()
        self._metrics = MetricsTracker()
        self._logger.info("系统已重置")
