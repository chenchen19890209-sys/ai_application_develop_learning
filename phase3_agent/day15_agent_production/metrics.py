"""
metrics.py — Agent 运行指标收集

功能：
1. AgentMetrics — 指标数据类（请求数、成功/失败、Token、响应时间）
2. MetricsCollector — 指标收集器（记录、查询、重置）

设计原则：零外部依赖，支持增量更新和导出
"""
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Dict


@dataclass
class AgentMetrics:
    """Agent 运行指标数据"""
    total_requests: int = 0       # 总请求数
    successful_requests: int = 0  # 成功请求数
    failed_requests: int = 0      # 失败请求数
    total_tokens_used: int = 0    # 总 Token 使用量
    avg_response_time: float = 0.0  # 平均响应时间（秒）
    tool_call_counts: Dict[str, int] = field(default_factory=dict)  # 各工具的调用次数

    @property
    def success_rate(self) -> float:
        """请求成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def failure_rate(self) -> float:
        """请求失败率"""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests


class MetricsCollector:
    """指标收集器 — 增量更新和导出"""

    def __init__(self):
        self._metrics = AgentMetrics()

    def record_request(self, success: bool = True, response_time: float = 0.0,
                       tokens_used: int = 0) -> None:
        """记录一次请求的指标"""
        self._metrics.total_requests += 1
        if success:
            self._metrics.successful_requests += 1
        else:
            self._metrics.failed_requests += 1

        # 移动平均更新响应时间
        n = self._metrics.total_requests
        old_avg = self._metrics.avg_response_time
        self._metrics.avg_response_time = old_avg + (response_time - old_avg) / n

        self._metrics.total_tokens_used += tokens_used

    def record_tool_call(self, tool_name: str) -> None:
        """记录一次工具调用"""
        if tool_name not in self._metrics.tool_call_counts:
            self._metrics.tool_call_counts[tool_name] = 0
        self._metrics.tool_call_counts[tool_name] += 1

    def get_report(self) -> dict:
        """获取完整的指标报告"""
        m = self._metrics
        return {
            "总请求数": m.total_requests,
            "成功请求": m.successful_requests,
            "失败请求": m.failed_requests,
            "成功率": f"{m.success_rate * 100:.1f}%",
            "失败率": f"{m.failure_rate * 100:.1f}%",
            "总 Token 数": m.total_tokens_used,
            "平均响应时间": f"{m.avg_response_time * 1000:.0f}ms",
            "工具调用统计": dict(m.tool_call_counts),
        }

    def reset(self) -> None:
        """重置所有指标"""
        self._metrics = AgentMetrics()


# ==================== 直接测试 ====================

if __name__ == "__main__":
    print("=" * 50)
    print("  指标系统测试")
    print("=" * 50)

    mc = MetricsCollector()

    # 模拟请求
    mc.record_request(success=True, response_time=0.15, tokens_used=120)
    mc.record_request(success=True, response_time=0.28, tokens_used=200)
    mc.record_request(success=False, response_time=1.5, tokens_used=50)
    mc.record_tool_call("search")
    mc.record_tool_call("search")
    mc.record_tool_call("calculate")

    print("  指标报告：")
    for key, value in mc.get_report().items():
        print(f"    {key}: {value}")
