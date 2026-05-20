"""
config.py — 生产级 Agent 配置管理

功能：
1. AgentConfig 数据类 — 集中管理所有生产配置
2. 支持环境变量覆盖 — 每个字段都可以通过环境变量覆盖
3. 合理的默认值 — 开箱即用

设计原则：配置与代码分离，所有敏感信息通过环境变量读取
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

# 导入项目共享配置
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL


@dataclass
class AgentConfig:
    """生产级 Agent 的集中配置"""

    # ── LLM 相关配置 ──
    api_key: str = OPENAI_API_KEY  # API 密钥
    base_url: str = OPENAI_BASE_URL  # API 地址
    model: str = OPENAI_MODEL  # 模型名称

    # ── 重试与超时 ──
    max_retries: int = 3  # 最大重试次数
    timeout: int = 30  # 请求超时（秒）

    # ── Agent 限制 ──
    max_iterations: int = 10  # 最大工具调用循环次数
    rate_limit: int = 60  # 每分钟最大请求数
    max_query_length: int = 2000  # 最大查询长度

    # ── 缓存配置 ──
    cache_ttl: int = 3600  # 缓存过期时间（秒）
    cache_max_size: int = 1000  # 最大缓存条目

    # ── 日志配置 ──
    log_level: str = "INFO"  # 日志级别

    # ── 断路器配置 ──
    circuit_breaker_threshold: int = 5  # 失败次数阈值
    circuit_breaker_timeout: int = 60  # 恢复超时（秒）

    # ── 指标上报 ──
    metrics_enabled: bool = True  # 是否启用指标收集

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """从环境变量创建配置（覆盖默认值）"""
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", OPENAI_API_KEY),
            base_url=os.getenv("OPENAI_BASE_URL", OPENAI_BASE_URL),
            model=os.getenv("OPENAI_MODEL", OPENAI_MODEL),
            max_retries=int(os.getenv("AGENT_MAX_RETRIES", "3")),
            timeout=int(os.getenv("AGENT_TIMEOUT", "30")),
            max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "10")),
            rate_limit=int(os.getenv("AGENT_RATE_LIMIT", "60")),
            max_query_length=int(os.getenv("AGENT_MAX_QUERY_LENGTH", "2000")),
            cache_ttl=int(os.getenv("AGENT_CACHE_TTL", "3600")),
            cache_max_size=int(os.getenv("AGENT_CACHE_MAX_SIZE", "1000")),
            circuit_breaker_threshold=int(os.getenv("CB_THRESHOLD", "5")),
            circuit_breaker_timeout=int(os.getenv("CB_TIMEOUT", "60")),
        )
