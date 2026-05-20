# Day 15: Agent 生产化 — 日志 / 缓存 / 重试 / 断路器 / 限流 / 验证 / 指标

> 🎯 **学习目标**
>
> - 理解生产级 Agent 的 7 大基础设施关注点
> - 掌握断路器模式：CLOSED → OPEN → HALF_OPEN 三态切换
> - 掌握指数退避重试和 TTL+LRU 缓存
> - 掌握结构化 JSON 日志和性能指标收集
> - 掌握输入验证和速率限制
> - 能构建一个真正"能扛"的生产级 Agent 系统

---

## 📖 前一天知识回顾

昨天我们实现了 Agent 编排系统：
- ✅ 工作流、管道、条件路由、自改进循环
- ✅ 零 LangGraph 依赖

**但是，一个只会在"理想环境"下运行的 Agent 不能叫生产级。** 生产环境会面临：API 偶尔故障、恶意输入、请求洪峰、成本失控……

**今天，我们给 Agent 装上"刹车、安全带、仪表盘"！**

---

## 📚 新知识讲解

### 1. 生产环境的 7 大关注点

**比喻**：Agent = 汽车引擎，生产基础设施 = 刹车/安全带/仪表盘/保险杠。

```
┌─────────────────────────────────────────────────────┐
│               ProductionAgent 9步执行管道             │
│                                                      │
│  输入 → [限流] → [验证] → [清洗] → [缓存检查]        │
│           ↓ 通过                                     │
│       [断路器] → [LLM调用(带重试)] → [缓存存储]       │
│           ↓                                          │
│       [指标记录] → [日志记录] → 输出                  │
└─────────────────────────────────────────────────────┘
```

### 2. 配置管理（rag_config.py）

见 [config.py](config.py) — `AgentConfig` 数据类：
- 所有参数集中管理，有合理默认值
- `__post_init__` 支持从环境变量覆盖
- `to_dict()` 导出时自动遮蔽敏感信息

### 3. 结构化日志（logger.py）

见 [logger.py](logger.py) — `AgentLogger` 类：

```json
{"timestamp": "2026-05-20T10:30:00", "level": "INFO", "component": "ProductionAgent",
 "message": "查询完成", "query": "...", "latency_ms": 234.5}
```

JSON 格式日志可直接被 ELK/Splunk/Loki 等日志聚合系统采集。

### 4. 断路器模式（resilience.py）

见 [resilience.py](resilience.py) — `CircuitBreaker` 类：

```
CLOSED ──(连续失败N次)──▶ OPEN ──(等待T秒)──▶ HALF_OPEN
   ▲                                              │
   └──────────(试探成功)──────────────────────────┘
              (试探失败)──────▶ OPEN
```

- **CLOSED**：正常状态，请求正常通过
- **OPEN**：断路器断开，直接拒绝所有请求（快速失败）
- **HALF_OPEN**：试探性恢复，允许少量请求通过

### 5. 指数退避重试

```python
@retry_with_backoff(max_retries=3, base_delay=1.0)
def call_llm():
    return client.chat.completions.create(...)
# 失败等待: 1s → 2s → 4s（每次翻倍）
```

### 6. TTL + LRU 缓存（cache.py）

见 [cache.py](cache.py) — `AgentCache` 类：
- **TTL**：每个缓存条目有生存时间，过期自动删除
- **LRU**：缓存满时淘汰"最久未使用"的条目
- **MD5 哈希**：查询文本 → 缓存键

### 7. 输入验证和速率限制（validation.py）

见 [validation.py](validation.py)：
- `InputValidator`：长度检查、HTML 标签剥离、注入模式检测（SQL/XSS 正则）
- `RateLimiter`：滑动窗口，每个 client_id 独立计数

### 8. 性能指标（metrics.py）

见 [metrics.py](metrics.py) — `MetricsCollector` 类：
- 请求总数、成功率、错误率
- 平均延迟、P50/P95 延迟（移动平均）
- 各工具使用频次统计

---

## 💡 实例演示

### 实例1：基础生产级查询

```python
from agent_system import ProductionAgent
agent = ProductionAgent()
result = agent.execute("搜索 AI 的信息")
# 自动经过: 限流→验证→清洗→缓存→断路器→LLM(重试)→缓存存储→指标→日志
```

### 实例2：缓存命中

```python
# 第1次 — 调用 LLM，耗时 ~2s
r1 = agent.execute("搜索 MCP 协议")

# 第2次 — 缓存命中，耗时 <0.01s，零 API 成本！
r2 = agent.execute("搜索 MCP 协议")
```

### 实例3：断路器触发

```python
from resilience import CircuitBreaker
cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5)
# 连续失败3次后自动断开，保护下游服务
```

### 实例4：健康检查

```python
health = agent.health_check()
# {"chromadb": "ok", "llm_api": "ok", "cache": "ok", "overall": "healthy"}
metrics = agent.get_metrics_report()
# {"total_requests": 10, "cache_hit_rate": 0.4, "p95_latency_ms": 1234.5}
```

完整演示见 [example.py](example.py)。

---

## ✍️ 练习题

### 练习1：基础题
1. 运行 `python example.py`，观察每个演示的输出
2. 修改 `AgentConfig` 的 `cache_ttl` 参数（从 3600 改为 10），观察缓存过期行为
3. 调整 `RateLimiter` 的窗口参数，测试不同限制策略

### 练习2：进阶题
1. 给 `ProductionAgent` 添加 "API 调用成本跟踪"：记录每次 LLM 调用的 token 消耗
2. 实现"优雅降级"：LLM 不可用时，返回基于缓存的静态回答
3. 给断路器添加告警回调：状态变为 OPEN 时触发通知函数

### 练习3：挑战题
1. 为 `ProductionAgent` 实现一个 Dashboard 类：实时打印 TPS、缓存命中率、错误率、P95 延迟的 ASCII 仪表盘
2. 实现"影子流量"模式：将 1% 的流量复制到新模型进行 A/B 对比

---

## 🔮 后一天知识展望

Phase 3（Agent 深度）到此结束！从 Day09 的 ReAct 基础到 Day15 的生产级系统，我们已经掌握了一个 Agent 从"能跑"到"能扛"的完整链路。

明天进入 **Phase 4: RAG 实战**（Day16）——将信息检索能力注入 Agent。我们先从 RAG 的原理和向量数据库开始。

---

## 📝 今日总结

- ✅ 生产基础设施 = 配置管理 + 日志 + 缓存 + 重试 + 断路器 + 限流 + 验证 + 指标
- ✅ 断路器保护下游依赖，避免级联故障（CLOSED→OPEN→HALF_OPEN）
- ✅ 指数退避重试应对瞬时故障（1s→2s→4s...）
- ✅ TTL+LRU 缓存减少重复 LLM 调用成本
- ✅ 结构化 JSON 日志便于 ELK/Splunk 采集和检索
- ✅ 输入验证防止注入攻击，速率限制保护 API 配额
- ✅ 所有组件独立、可测试、零框架依赖

---

## 🚀 下一步

1. 完成所有练习题
2. 回顾 Phase 3 全部 5 天内容（Day11-15），确保理解 Agent 完整链路
3. 思考：你当前的项目中缺乏哪些生产基础设施？

---

## 📖 参考资料

- [Microsoft - Circuit Breaker Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)
- [AWS - Exponential Backoff and Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [12-Factor App](https://12factor.net/)（配置管理最佳实践）
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [Structured Logging (thoughtworks)](https://www.thoughtworks.com/radar/techniques/structured-logging)
