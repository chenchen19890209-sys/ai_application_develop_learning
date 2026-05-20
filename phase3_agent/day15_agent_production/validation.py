"""
validation.py — 输入验证与速率限制

功能：
1. InputValidator — 查询长度验证、HTML/脚本注入防护
2. RateLimiter — 基于滑动窗口的速率限制

设计原则：在入口处拦截无效和恶意请求，保护 Agent 系统安全
"""
import time
import re
from collections import defaultdict


class InputValidator:
    """输入验证器 — 检查和清理用户输入"""

    def __init__(self, max_length: int = 2000):
        self.max_length = max_length  # 最大查询长度

    def validate_length(self, query: str) -> bool:
        """检查查询长度是否在允许范围内"""
        if not query or not query.strip():
            return False
        return len(query) <= self.max_length

    def sanitize(self, query: str) -> str:
        """清理输入 — 去除 HTML 标签、危险字符"""
        # 去除 HTML 标签
        clean = re.sub(r"<[^>]*>", "", query)
        # 去除多余空白
        clean = re.sub(r"\s+", " ", clean).strip()
        # 截断到最大长度
        if len(clean) > self.max_length:
            clean = clean[:self.max_length]
        return clean

    def check_injection(self, query: str) -> bool:
        """检查基本的注入模式"""
        # 检测常见的注入模式
        patterns = [
            r"\{\{.*\}\}",           # Jinja2 模板注入
            r"\$\{.*\}",             # Shell 变量注入
            r"(?:DROP|DELETE)\s+",   # SQL 语句
            r"<script.*>",           # XSS
            r"system\s*\(",          # 命令执行
        ]
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False

    def validate(self, query: str) -> tuple:
        """综合验证：返回 (是否有效, 清理后的查询, 错误信息)"""
        if not query or not query.strip():
            return False, "", "查询为空"

        if len(query) > self.max_length:
            return False, "", f"查询过长（{len(query)}/{self.max_length} 字符）"

        if self.check_injection(query):
            return False, "", "检测到潜在的注入攻击"

        clean = self.sanitize(query)
        return True, clean, ""


class RateLimiter:
    """滑动窗口速率限制器"""

    def __init__(self, max_requests: int = 60, window_seconds: float = 60.0):
        self.max_requests = max_requests     # 窗口内最大请求数
        self.window_seconds = window_seconds  # 时间窗口（秒）
        self._clients = defaultdict(list)     # client_id → [request_timestamps]

    def is_allowed(self, client_id: str = "default") -> bool:
        """检查是否允许该客户端的请求"""
        now = time.time()
        timestamps = self._clients[client_id]

        # 清理过期的时间戳（滑动窗口）
        window_start = now - self.window_seconds
        self._clients[client_id] = [t for t in timestamps if t > window_start]

        # 检查是否超限
        if len(self._clients[client_id]) >= self.max_requests:
            return False

        # 记录当前请求
        self._clients[client_id].append(now)
        return True

    def get_remaining(self, client_id: str = "default") -> int:
        """获取剩余可用请求数"""
        now = time.time()
        window_start = now - self.window_seconds
        self._clients[client_id] = [t for t in self._clients.get(client_id, []) if t > window_start]
        return max(0, self.max_requests - len(self._clients[client_id]))

    def reset(self, client_id: str = "default") -> None:
        """重置指定客户端的速率限制"""
        if client_id in self._clients:
            del self._clients[client_id]


# ==================== 直接测试 ====================

if __name__ == "__main__":
    print("=" * 50)
    print("  验证系统测试")
    print("=" * 50)

    # 测试输入验证
    print("\n📋 1. 输入验证:")
    validator = InputValidator(max_length=500)

    valid, clean, err = validator.validate("正常的查询")
    print(f"  正常查询: valid={valid}, clean='{clean}'")

    valid, clean, err = validator.validate("<script>alert('xss')</script>")
    print(f"  XSS 查询: valid={valid}, err='{err}'")

    valid, clean, err = validator.validate("DROP TABLE users")
    print(f"  SQL 注入: valid={valid}, err='{err}'")

    # 测试速率限制
    print("\n📋 2. 速率限制:")
    rl = RateLimiter(max_requests=3, window_seconds=10)

    for i in range(5):
        allowed = rl.is_allowed("test_user")
        status = "✓ 通过" if allowed else "✗ 拒绝"
        print(f"  请求 {i+1}: {status}（剩余: {rl.get_remaining('test_user')}）")
