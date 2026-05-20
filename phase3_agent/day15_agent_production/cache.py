"""
cache.py — TTL + LRU 缓存系统

功能：
1. AgentCache — 带 TTL 过期和 LRU 淘汰的内存缓存
2. MD5 键哈希 — 支持任意长度的查询键
3. 缓存命中统计 — get/set/hit_rate

设计原则：零外部依赖，适合单进程 Agent 使用
"""
import time
import hashlib
from collections import OrderedDict
from typing import Optional


class AgentCache:
    """TTL 过期 + LRU 淘汰的内存缓存"""

    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        self.ttl = ttl                # 缓存过期时间（秒）
        self.max_size = max_size      # 最大缓存条目数
        self._store = OrderedDict()   # 有序字典（实现 LRU）
        self._hits = 0               # 命中次数
        self._misses = 0             # 未命中次数

    def _generate_key(self, key: str) -> str:
        """生成 MD5 哈希键 — 统一键长度，支持长查询"""
        return hashlib.md5(key.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[str]:
        """获取缓存值（检查 TTL 过期）"""
        cache_key = self._generate_key(key)
        if cache_key not in self._store:
            self._misses += 1
            return None

        entry = self._store[cache_key]
        # 检查 TTL 过期
        if time.time() - entry["timestamp"] > self.ttl:
            del self._store[cache_key]
            self._misses += 1
            return None

        # LRU：将访问的条目移到末尾（最近使用）
        self._store.move_to_end(cache_key)
        self._hits += 1
        return entry["value"]

    def set(self, key: str, value: str) -> None:
        """存入缓存值"""
        cache_key = self._generate_key(key)

        # LRU 淘汰：达到上限时删除最旧的条目
        if len(self._store) >= self.max_size:
            self._store.popitem(last=False)  # 删除第一个（最久未使用）

        self._store[cache_key] = {
            "value": value,
            "timestamp": time.time()
        }
        # 移到末尾（最近使用）
        self._store.move_to_end(cache_key)

    def clear(self) -> None:
        """清空所有缓存"""
        self._store.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        total = self._hits + self._misses
        return {
            "size": len(self._store),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{self._hits / total * 100:.1f}%" if total > 0 else "0%",
            "utilization": f"{len(self._store) / self.max_size * 100:.1f}%",
        }


# ==================== 直接测试 ====================

if __name__ == "__main__":
    print("=" * 50)
    print("  缓存系统测试")
    print("=" * 50)

    cache = AgentCache(ttl=2, max_size=3)  # TTL=2s, 最多 3 条

    # 测试基本读写
    cache.set("query1", "答案1")
    print(f"  get('query1'): {cache.get('query1')}")

    # 测试过期
    print("  等待 3 秒让缓存过期...")
    time.sleep(3)
    print(f"  get('query1') 过期后: {cache.get('query1')}")

    # 测试 LRU 淘汰
    cache.set("a", "A")
    cache.set("b", "B")
    cache.set("c", "C")
    cache.set("d", "D")  # 应该淘汰最旧的 "a"
    print(f"  LRU 淘汰后 get('a'): {cache.get('a')}")
    print(f"  LRU 淘汰后 get('d'): {cache.get('d')}")

    # 统计
    print(f"  缓存统计: {cache.get_stats()}")
