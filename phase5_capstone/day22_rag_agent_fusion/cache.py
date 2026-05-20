"""
cache.py — Day 22 RAG Agent 缓存模块

实现 TTL + LRU 双层缓存策略：
- TTL（Time-To-Live）：缓存条目过期自动失效
- LRU（Least Recently Used）：容量满时淘汰最久未使用的条目

用途：缓存 RAG 检索结果，避免重复查询向量数据库。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import time
import hashlib
from typing import Optional, Dict, Any, List
from collections import OrderedDict
from models import RAGResult


class RAGAgentCache:
    """RAG Agent 缓存 — TTL + LRU 双层缓存

    使用场景：
    - 用户在对话中反复提到同一主题 → 命中缓存，无需重复检索
    - 高频问题（如"什么是 RAG"）→ 缓存直接命中

    缓存键 = MD5(查询文本)，确保相同查询命中同一缓存条目。
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        """
        Args:
            max_size: 最大缓存条目数（LRU 淘汰阈值）
            ttl_seconds: 缓存过期时间（秒），默认 5 分钟
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        # OrderedDict 实现 LRU：最近访问的条目移到末尾
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._hits = 0      # 缓存命中次数
        self._misses = 0    # 缓存未命中次数

    def _make_key(self, query: str) -> str:
        """生成缓存键 — MD5 哈希确保键名稳定"""
        return hashlib.md5(query.encode("utf-8")).hexdigest()

    def get(self, query: str) -> Optional[List[RAGResult]]:
        """从缓存获取检索结果

        Args:
            query: 查询文本

        Returns:
            命中的 RAGResult 列表，未命中返回 None
        """
        key = self._make_key(query)
        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]
        # 检查 TTL 是否过期
        if time.time() - entry["timestamp"] > self.ttl_seconds:
            del self._cache[key]
            self._misses += 1
            return None

        # LRU：将访问的条目移到末尾
        self._cache.move_to_end(key)
        self._hits += 1
        return entry["results"]

    def set(self, query: str, results: List[RAGResult]):
        """将检索结果存入缓存

        Args:
            query: 查询文本
            results: RAG 检索结果列表
        """
        key = self._make_key(query)
        # LRU 淘汰：超过最大容量时删除最旧的条目
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)

        self._cache[key] = {
            "query": query,
            "results": results,
            "timestamp": time.time(),
        }
        # LRU：新条目放在末尾（最近使用）
        self._cache.move_to_end(key)

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    @property
    def stats(self) -> Dict[str, Any]:
        """缓存统计信息"""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1%}",
            "ttl_seconds": self.ttl_seconds,
        }
