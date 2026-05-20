"""
rag_config.py — 生产级 RAG 配置管理

功能：
1. RAGConfig 数据类 — 集中管理所有可调参数
2. 提供合理的生产级默认值
3. 支持从环境变量覆盖（12-Factor App 原则）

设计原则：
- 使用 @dataclass 实现零样板代码的配置类
- 所有参数有默认值，开箱即用
- 通过 from_env() 类方法支持环境变量注入
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RAGConfig:
    """生产级 RAG 系统配置 — 所有可调参数集中管理

    配置分类:
    - 嵌入与分块: embedding_model, chunk_size, chunk_overlap
    - 检索: top_k, use_hybrid, hybrid_weight
    - 重排序: use_reranker, reranker_model
    - 缓存: cache_ttl, cache_max_size
    - 可靠性: max_retries, retry_delay
    - 可观测性: log_level, collect_metrics
    - 存储: collection_name, db_path
    """

    # ========== 嵌入模型配置 ==========
    embedding_model: str = "BAAI/bge-small-zh-v1.5"  # 中文嵌入模型名称（HuggingFace）

    # ========== 文档分块配置 ==========
    chunk_size: int = 500        # 每个文档块的目标字符数
    chunk_overlap: int = 100     # 相邻块之间的重叠字符数（避免语义断裂）

    # ========== 检索配置 ==========
    top_k: int = 5               # 检索返回的文档块数量
    use_hybrid: bool = True      # 是否启用混合检索（向量+BM25关键字→RRF融合）
    hybrid_weight: float = 0.5   # 混合检索中向量分数的权重（0=纯BM25, 1=纯向量）

    # ========== 重排序配置 ==========
    use_reranker: bool = True    # 是否启用 Cross-Encoder 重排序
    reranker_model: str = "BAAI/bge-reranker-base"  # 重排序模型名称

    # ========== 向量数据库配置 ==========
    collection_name: str = "production_rag"  # ChromaDB 集合名称
    db_path: str = ""            # 向量库持久化路径（空字符串 = 自动生成）

    # ========== 缓存配置 ==========
    cache_ttl: int = 3600        # 缓存生存时间（秒），默认 1 小时
    cache_max_size: int = 1000   # 缓存最大条目数（超出时 LRU 淘汰）

    # ========== 重试配置 ==========
    max_retries: int = 3         # API 调用失败的最大重试次数
    retry_delay: float = 1.0     # 初始重试等待时间（秒），每次翻倍（指数退避）

    # ========== LLM 生成配置 ==========
    temperature: float = 0.3     # 生成温度（0-1），越低越确定性
    max_tokens: int = 1024       # 生成的最大 token 数

    # ========== 可观测性配置 ==========
    log_level: str = "INFO"      # 日志级别: DEBUG/INFO/WARNING/ERROR
    collect_metrics: bool = True # 是否收集性能指标（延迟、命中率等）

    # ========== 环境相关配置 ==========
    request_timeout: int = 30    # API 请求超时时间（秒）

    @classmethod
    def from_env(cls) -> "RAGConfig":
        """从环境变量创建配置 — 适用于容器化部署（12-Factor App）

        支持的环境变量:
        - RAG_CACHE_TTL: 缓存 TTL（秒）
        - RAG_CACHE_MAX_SIZE: 缓存最大条目
        - RAG_MAX_RETRIES: 最大重试次数
        - RAG_LOG_LEVEL: 日志级别
        - RAG_USE_HYBRID: 是否启用混合检索（true/false）
        - RAG_USE_RERANKER: 是否启用重排序（true/false）
        """
        import os  # 延迟导入，避免全局污染

        config = cls()  # 先创建默认配置

        # 从环境变量覆盖配置值
        if os.getenv("RAG_CACHE_TTL"):
            config.cache_ttl = int(os.getenv("RAG_CACHE_TTL"))
        if os.getenv("RAG_CACHE_MAX_SIZE"):
            config.cache_max_size = int(os.getenv("RAG_CACHE_MAX_SIZE"))
        if os.getenv("RAG_MAX_RETRIES"):
            config.max_retries = int(os.getenv("RAG_MAX_RETRIES"))
        if os.getenv("RAG_LOG_LEVEL"):
            config.log_level = os.getenv("RAG_LOG_LEVEL")
        if os.getenv("RAG_USE_HYBRID") is not None:
            config.use_hybrid = os.getenv("RAG_USE_HYBRID").lower() in ("true", "1", "yes")
        if os.getenv("RAG_USE_RERANKER") is not None:
            config.use_reranker = os.getenv("RAG_USE_RERANKER").lower() in ("true", "1", "yes")

        return config

    def to_dict(self) -> dict:
        """将配置导出为字典 — 便于日志记录和序列化"""
        return {
            "embedding_model": self.embedding_model,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "top_k": self.top_k,
            "use_hybrid": self.use_hybrid,
            "use_reranker": self.use_reranker,
            "cache_ttl": self.cache_ttl,
            "cache_max_size": self.cache_max_size,
            "max_retries": self.max_retries,
            "log_level": self.log_level,
            "collection_name": self.collection_name,
        }
