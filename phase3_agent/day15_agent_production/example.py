"""
example.py — Day 15 完整演示：Agent 生产化

演示内容：
1. 基础生产 Agent — 单次真实 LLM 查询
2. 缓存命中 — 重复查询从缓存返回
3. 断路器触发 — 连续失败后自动断开
4. 重试机制 — 指数退避自动重试
5. 速率限制 — 超过限制被拒绝
6. 健康检查 + 指标报告
7. 复杂多工具查询
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import time
from config import AgentConfig
from agent_system import ProductionAgent
from resilience import retry_with_backoff


def demo_basic_query():
    """演示 1：基础生产级查询"""
    print("\n" + "=" * 60)
    print("  📋 演示 1：基础生产级查询")
    print("=" * 60)

    agent = ProductionAgent()
    queries = [
        "搜索 AI 的信息",
        "北京天气怎么样",
        "计算 25 * 4 + 10",
    ]

    for q in queries:
        print(f"\n  👤 查询: {q}")
        try:
            result = agent.execute(q)
            if result["success"]:
                print(f"  ✅ 回答: {result['answer'][:200]}...")
                print(f"  ⏱ 耗时: {result['duration']:.2f}s")
                print(f"  📦 来自缓存: {result['from_cache']}")
            else:
                print(f"  ❌ 错误: {result['error']}")
        except Exception as e:
            print(f"  ⚠️ 执行失败: {e}")

    agent.cleanup()


def demo_cache():
    """演示 2：缓存命中"""
    print("\n" + "=" * 60)
    print("  📋 演示 2：缓存命中演示")
    print("=" * 60)

    agent = ProductionAgent()
    query = "搜索 MCP 协议"

    print(f"\n  🔄 第 1 次查询（应调用 LLM）...")
    t1 = time.time()
    r1 = agent.execute(query)
    print(f"  📦 来自缓存: {r1.get('from_cache')}，耗时: {r1.get('duration', 0):.2f}s")

    print(f"\n  🔄 第 2 次查询（应命中缓存）...")
    t2 = time.time()
    r2 = agent.execute(query)
    print(f"  📦 来自缓存: {r2.get('from_cache')}，耗时: {r2.get('duration', 0):.2f}s")

    print(f"\n  💡 缓存命中时几乎不消耗 API 调用成本，延迟极低")

    print(f"\n  📊 缓存统计: {agent.cache.get_stats()}")
    agent.cleanup()


def demo_circuit_breaker():
    """演示 3：断路器模式"""
    print("\n" + "=" * 60)
    print("  📋 演示 3：断路器触发")
    print("=" * 60)

    print("  (此演示通过模拟失败展示断路器的状态转换)")

    from resilience import CircuitBreaker
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5)

    print(f"\n  初始状态: {cb.state}")
    for i in range(5):
        if cb.can_execute():
            if i < 3:
                cb.record_failure()
                print(f"  ❌ 请求 {i+1}: 失败 → 状态={cb.state}, 失败计数={cb.failure_count}")
            else:
                print(f"  🛑 请求 {i+1}: 断路器已断开，请求被拒绝")
        else:
            print(f"  🛑 请求 {i+1}: 断路器断开，直接拒绝")

    print(f"\n  等待 {cb.recovery_timeout}s 恢复...")
    print(f"  (实际场景中会等待 recovery_timeout 后进入 HALF_OPEN)")
    print(f"\n  💡 断路器保护: 在依赖服务故障时快速失败，避免级联故障")


def demo_retry():
    """演示 4：重试机制"""
    print("\n" + "=" * 60)
    print("  📋 演示 4：指数退避重试")
    print("=" * 60)

    call_count = [0]  # 使用列表来在闭包中修改

    @retry_with_backoff(max_retries=3, base_delay=0.3)
    def unreliable_operation():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ConnectionError(f"模拟连接失败（第 {call_count[0]} 次）")
        return f"操作成功（第 {call_count[0]} 次尝试）"

    try:
        result = unreliable_operation()
        print(f"  ✅ {result}")
        print(f"  💡 前 2 次失败自动重试，第 3 次成功")
    except Exception as e:
        print(f"  ❌ {e}")

    # 测试全部失败
    print(f"\n  -- 全部失败的情况 --")
    call_count[0] = 0

    @retry_with_backoff(max_retries=2, base_delay=0.2)
    def always_fails():
        call_count[0] += 1
        raise RuntimeError(f"永久失败（第 {call_count[0]} 次）")

    try:
        always_fails()
    except RuntimeError as e:
        print(f"  ❌ 所有重试都失败: {e}")


def demo_rate_limiting():
    """演示 5：速率限制"""
    print("\n" + "=" * 60)
    print("  📋 演示 5：速率限制")
    print("=" * 60)

    from validation import RateLimiter
    rl = RateLimiter(max_requests=3, window_seconds=30)

    print(f"\n  限制: 每 30 秒最多 3 次请求")
    for i in range(5):
        allowed = rl.is_allowed("demo_user")
        remaining = rl.get_remaining("demo_user")
        status = "✓" if allowed else "✗ 被拒绝"
        print(f"  请求 {i+1}: {status}（剩余配额: {remaining}）")

    print(f"\n  💡 速率限制防止 API 过度调用，控制成本")


def demo_health_check():
    """演示 6：健康检查和指标"""
    print("\n" + "=" * 60)
    print("  📋 演示 6：健康检查 + 指标报告")
    print("=" * 60)

    agent = ProductionAgent()

    # 执行几次查询以生成指标
    queries = ["搜索 AI", "北京天气", "计算 100+200"]
    for q in queries:
        try:
            agent.execute(q)
        except Exception:
            pass

    print(f"\n  🏥 健康检查:")
    for k, v in agent.health_check().items():
        print(f"    {k}: {v}")

    print(f"\n  📊 指标报告:")
    for k, v in agent.get_metrics_report().items():
        if isinstance(v, dict):
            print(f"    {k}:")
            for sub_k, sub_v in v.items():
                print(f"      {sub_k}: {sub_v}")
        else:
            print(f"    {k}: {v}")

    agent.cleanup()


def main():
    """主函数"""
    print("=" * 60)
    print("  Day 15: Agent 生产化")
    print("  日志 | 缓存 | 重试 | 断路器 | 限流 | 验证 | 指标")
    print("=" * 60)
    print("  ⚡ 零 LangChain 依赖 — 纯 Python + openai SDK")
    print("=" * 60)

    try:
        demo_retry()              # 不需要 LLM
        demo_rate_limiting()      # 不需要 LLM
        demo_circuit_breaker()    # 不需要 LLM
        demo_health_check()       # 需要 LLM（可选跳过）
        demo_cache()              # 需要 LLM
        demo_basic_query()        # 需要 LLM

        print("\n" + "=" * 60)
        print("  ✅ 所有演示完成！")
        print("=" * 60)
        print("\n  💡 Day 15 关键要点：")
        print("    1. 生产级 Agent = 业务逻辑 + 基础设施关注点")
        print("    2. 日志 — 结构化 JSON 日志，便于分析排查")
        print("    3. 缓存 — TTL+LRU 缓存，减少重复 LLM 调用成本")
        print("    4. 重试 — 指数退避，处理瞬时故障")
        print("    5. 断路器 — 快速失败，保护下游依赖")
        print("    6. 速率限制 — 保护 API 配额，控制成本")
        print("    7. 输入验证 — 防止注入攻击，保证输入质量")
        print("    8. 指标 — 监控请求成功率、响应时间、工具使用")

    except Exception as e:
        print(f"\n  ❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
