"""
resilience.py — 弹性模式：重试 + 断路器

功能：
1. retry_with_backoff — 指数退避重试装饰器
2. CircuitBreaker — 三态断路器（CLOSED/OPEN/HALF_OPEN）

设计原则：
- 零外部依赖，纯 Python 标准库实现
- 重试策略：指数退避（1s, 2s, 4s, 8s...）
- 断路器：保护下游服务，快速失败优于长时间等待
"""
import time
import functools
from typing import Callable


# ==================== 指数退避重试 ====================

def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0,
                        exceptions: tuple = (Exception,)):
    """
    指数退避重试装饰器

    参数：
        max_retries: 最大重试次数（不含首次调用）
        base_delay: 基础延迟时间（秒），每次重试延迟翻倍
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)  # 指数退避
                        print(f"  🔄 重试 {attempt + 1}/{max_retries}: {e}，等待 {delay:.1f}s...")
                        time.sleep(delay)
                    else:
                        print(f"  ❌ 所有重试均已用尽: {e}")
            raise last_exception
        return wrapper
    return decorator


# ==================== 断路器 ====================

class CircuitBreaker:
    """
    三态断路器

    状态转换：
    CLOSED → (失败数达阈值) → OPEN
    OPEN → (超时结束) → HALF_OPEN
    HALF_OPEN → (成功) → CLOSED
    HALF_OPEN → (失败) → OPEN
    """

    CLOSED = "CLOSED"       # 正常状态，请求通过
    OPEN = "OPEN"           # 断开状态，直接拒绝
    HALF_OPEN = "HALF_OPEN"  # 半开状态，试探性放行

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold  # 连续失败 N 次后断开
        self.recovery_timeout = recovery_timeout     # 断开后等待（秒）再半开

        self.state = self.CLOSED            # 当前状态
        self.failure_count = 0             # 连续失败计数
        self.last_failure_time = None      # 最后一次失败的时间
        self.total_successes = 0           # 总成功次数
        self.total_failures = 0            # 总失败次数

    def can_execute(self) -> bool:
        """检查是否允许执行"""
        if self.state == self.CLOSED:
            return True
        elif self.state == self.OPEN:
            # 检查是否超过恢复超时
            if self.last_failure_time and \
               time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = self.HALF_OPEN
                self.failure_count = 0
                print(f"  ⚡ 断路器: OPEN → HALF_OPEN（试探性恢复）")
                return True
            return False
        elif self.state == self.HALF_OPEN:
            return True
        return True

    def record_success(self) -> None:
        """记录一次成功的执行"""
        self.total_successes += 1
        if self.state == self.HALF_OPEN:
            self.state = self.CLOSED
            self.failure_count = 0
            print(f"  ⚡ 断路器: HALF_OPEN → CLOSED（已恢复）")
        elif self.state == self.CLOSED:
            self.failure_count = 0  # 成功时重置失败计数

    def record_failure(self) -> None:
        """记录一次失败的执行"""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == self.HALF_OPEN:
            self.state = self.OPEN
            print(f"  ⚡ 断路器: HALF_OPEN → OPEN（试探失败）")
        elif self.state == self.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = self.OPEN
            print(f"  ⚡ 断路器: CLOSED → OPEN（连续 {self.failure_count} 次失败，断开 {self.recovery_timeout}s）")

    def get_status(self) -> dict:
        """获取断路器状态信息"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "threshold": self.failure_threshold,
            "is_open": self.state == self.OPEN,
        }


# ==================== 直接测试 ====================

if __name__ == "__main__":
    print("=" * 50)
    print("  弹性模式测试")
    print("=" * 50)

    # 测试重试
    print("\n📋 1. 重试测试:")

    @retry_with_backoff(max_retries=2, base_delay=0.1)
    def flaky_function(should_fail: bool = True):
        if should_fail:
            raise ValueError("模拟失败")
        return "成功"

    try:
        result = flaky_function(should_fail=False)
        print(f"  ✅ {result}")
    except Exception as e:
        print(f"  ❌ {e}")

    # 测试断路器
    print("\n📋 2. 断路器测试:")
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5)

    for i in range(5):
        if not cb.can_execute():
            print(f"  🛑 断路器断开，拒绝请求")
            break
        if i < 2:
            cb.record_failure()
            print(f"  ❌ 失败 {i+1}: 状态={cb.state}")
        else:
            cb.record_success()
            print(f"  ✅ 成功: 状态={cb.state}")

    print(f"  断路器状态: {cb.get_status()}")
