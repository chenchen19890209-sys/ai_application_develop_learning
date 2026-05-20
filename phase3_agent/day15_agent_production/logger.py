"""
logger.py — 结构化 JSON 日志系统

功能：
1. AgentLogger — 生产级的结构化日志记录器
2. 同时输出到文件和控制台
3. JSON 格式 — 便于日志聚合和分析
4. 自动记录时间戳、请求/响应长度、耗时等关键指标

设计原则：日志不阻塞 Agent 执行，所有异常都被安全处理
"""
import logging
import json
import time
from datetime import datetime
from typing import Optional


class AgentLogger:
    """结构化 JSON 日志记录器"""

    def __init__(self, name: str = "ProductionAgent", log_file: str = "agent.log",
                 level: str = "INFO"):
        self.name = name

        # 创建 logger
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        # 避免重复添加 handler
        if not self._logger.handlers:
            # 文件处理器 — 记录所有 INFO 及以上
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(file_handler)

            # 控制台处理器 — 只显示 WARNING 及以上
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
            self._logger.addHandler(console_handler)

    def log_action(self, agent_id: str, action: str,
                   input_data: str = "", output_data: str = "",
                   duration: float = 0.0, **extra) -> None:
        """记录一次 Agent 操作的结构化日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "action": action,
            "input_length": len(input_data),
            "output_length": len(output_data),
            "duration_ms": round(duration * 1000, 2),
        }
        log_entry.update(extra)  # 合并额外字段
        self._logger.info(json.dumps(log_entry, ensure_ascii=False))

    def log_error(self, agent_id: str, error_type: str,
                  error_message: str, context: str = "", **extra) -> None:
        """记录错误的结构化日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "level": "ERROR",
            "error_type": error_type,
            "error_message": error_message,
            "context": context[:500],  # 截断过长上下文
        }
        log_entry.update(extra)
        self._logger.error(json.dumps(log_entry, ensure_ascii=False))

    def log_warning(self, agent_id: str, message: str, **extra) -> None:
        """记录警告的结构化日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "level": "WARNING",
            "message": message,
        }
        log_entry.update(extra)
        self._logger.warning(json.dumps(log_entry, ensure_ascii=False))

    def log_debug(self, agent_id: str, message: str, **extra) -> None:
        """记录调试的结构化日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "level": "DEBUG",
            "message": message,
        }
        log_entry.update(extra)
        self._logger.debug(json.dumps(log_entry, ensure_ascii=False))


# ==================== 直接测试 ====================

if __name__ == "__main__":
    print("=" * 50)
    print("  日志系统测试")
    print("=" * 50)

    logger = AgentLogger("TestAgent", log_file="test_agent.log")
    logger.log_action("agent-001", "test_query", input_data="你好", output_data="你好！", duration=0.15)
    logger.log_error("agent-001", "APIError", "模拟 API 错误", context="测试上下文")
    logger.log_warning("agent-001", "缓存即将过期", ttl_remaining=60)
    print("✅ 日志已写入 test_agent.log")
