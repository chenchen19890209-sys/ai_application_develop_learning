"""
agent_system.py — 生产级 Agent 系统（真实 LLM 调用）

功能：
1. ProductionAgent — 集成所有生产关注点的完整 Agent
2. 执行管道：速率限制 → 验证 → 缓存 → 断路器 → LLM → 指标 → 日志
3. 真实 LLM 调用 — 使用原生 openai SDK，支持工具调用循环

设计原则：
- 所有生产关注点与业务逻辑解耦
- 组件可独立测试和替换
- 零 LangChain 依赖
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import AgentConfig
from logger import AgentLogger
from resilience import retry_with_backoff, CircuitBreaker
from cache import AgentCache
from metrics import MetricsCollector
from validation import InputValidator, RateLimiter
from tools import get_production_tools, find_tool, tools_to_openai_format

from openai import OpenAI
import json
import time


class ProductionAgent:
    """
    生产级 Agent — 集成所有生产基础设施

    执行管道（按顺序）：
    1️⃣  速率限制检查 → 拒绝超限请求
    2️⃣  输入验证 → 拒绝无效/恶意输入
    3️⃣  输入清洗 → 去除危险内容
    4️⃣  缓存查找 → 返回命中结果
    5️⃣  断路器检查 → 系统故障时快速失败
    6️⃣  真实 LLM 调用 → 带工具调用循环
    7️⃣  缓存存储 → 保存结果供后续使用
    8️⃣  指标记录 → 更新请求统计
    9️⃣  结构化日志 → JSON 格式记录
    """

    def __init__(self, config: AgentConfig = None):
        # 配置
        self.config = config or AgentConfig()

        # 初始化所有组件
        self.logger = AgentLogger("ProductionAgent", self.config.log_file, self.config.log_level)
        self.cache = AgentCache(ttl=self.config.cache_ttl, max_size=self.config.cache_max_size)
        self.metrics = MetricsCollector()
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.circuit_breaker_threshold,
            recovery_timeout=self.config.circuit_breaker_timeout
        )
        self.rate_limiter = RateLimiter(max_requests=self.config.rate_limit)
        self.validator = InputValidator(max_length=self.config.max_query_length)

        # 工具
        self.tools = get_production_tools()
        self._openai_tools = tools_to_openai_format(self.tools)

        # LLM 客户端
        self.client = OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)

        # Agent 标识
        self.agent_id = f"agent-{id(self):x}"[-12:]

    def execute(self, query: str, client_id: str = "default") -> dict:
        """完整的生产级执行管道"""
        start_time = time.time()

        # 1️⃣ 速率限制检查
        if not self.rate_limiter.is_allowed(client_id):
            err_msg = f"速率限制：超过 {self.config.rate_limit} 次/分钟"
            print(f"  🚫 {err_msg}")
            self.logger.log_warning(self.agent_id, err_msg, client_id=client_id)
            return {"success": False, "error": err_msg, "from_cache": False}

        # 2️⃣ 输入验证
        valid, clean_query, err_msg = self.validator.validate(query)
        if not valid:
            print(f"  🚫 输入验证失败: {err_msg}")
            self.logger.log_warning(self.agent_id, "输入验证失败", reason=err_msg)
            return {"success": False, "error": err_msg, "from_cache": False}
        query = clean_query

        # 3️⃣ 缓存查找
        cached = self.cache.get(query)
        if cached is not None:
            elapsed = time.time() - start_time
            print(f"  ⚡ 缓存命中！")
            self.metrics.record_request(success=True, response_time=elapsed)
            self.logger.log_action(self.agent_id, "cache_hit", input_data=query,
                                   output_data=cached, duration=elapsed)
            return {"success": True, "answer": cached, "from_cache": True, "duration": elapsed}

        # 4️⃣ 断路器检查
        if not self.circuit_breaker.can_execute():
            err_msg = "断路器已断开，系统暂时不可用"
            print(f"  🛑 {err_msg}")
            self.logger.log_error(self.agent_id, "CircuitBreakerOpen", err_msg)
            return {"success": False, "error": err_msg, "from_cache": False}

        # 5️⃣ 真实 LLM 调用
        try:
            print(f"  🤖 调用 LLM: {self.config.model}")
            llm_result = self._call_llm_with_tools(query)
            self.circuit_breaker.record_success()
        except Exception as e:
            self.circuit_breaker.record_failure()
            elapsed = time.time() - start_time
            self.metrics.record_request(success=False, response_time=elapsed)
            self.logger.log_error(self.agent_id, type(e).__name__, str(e), context=query[:200])
            return {"success": False, "error": f"LLM 调用失败: {str(e)}", "from_cache": False, "duration": elapsed}

        # 6️⃣ 缓存存储
        self.cache.set(query, llm_result)

        # 7️⃣ 指标记录
        elapsed = time.time() - start_time
        self.metrics.record_request(success=True, response_time=elapsed)

        # 8️⃣ 结构化日志
        self.logger.log_action(self.agent_id, "execute", input_data=query,
                               output_data=llm_result, duration=elapsed)

        return {"success": True, "answer": llm_result, "from_cache": False, "duration": elapsed}

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def _call_llm_with_tools(self, query: str) -> str:
        """真实 LLM 调用 — 包含完整的工具调用循环"""
        messages = [
            {"role": "system", "content": (
                "你是一个生产级 AI 助手。使用工具获取信息，给出准确、简洁的回复。"
                "可以使用 search 工具搜索知识库、calculate 工具计算、get_weather 工具查询天气。"
            )},
            {"role": "user", "content": query}
        ]

        for iteration in range(self.config.max_iterations):
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                tools=self._openai_tools,
                tool_choice="auto",
                temperature=0.3
            )

            msg = response.choices[0].message

            # 记录 Token 使用
            if hasattr(response, "usage") and response.usage:
                self.metrics.record_request(tokens_used=response.usage.total_tokens)

            # 无工具调用 → 返回结果
            if not msg.tool_calls:
                return msg.content or "任务完成"

            # 执行工具调用
            messages.append(msg)
            for tc in msg.tool_calls:
                tool = find_tool(self.tools, tc.function.name)
                args = json.loads(tc.function.arguments)
                if tool:
                    print(f"  🔧 工具调用: {tc.function.name}({json.dumps(args, ensure_ascii=False)})")
                    self.metrics.record_tool_call(tc.function.name)
                    result = tool.execute(**args)
                    tool_output = result["content"][0]["text"]
                    print(f"  📤 工具结果: {tool_output[:100]}...")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_output
                    })

        return "Agent 执行超时"

    def get_metrics_report(self) -> dict:
        """获取完整指标报告（含缓存统计和断路器状态）"""
        report = self.metrics.get_report()
        report["缓存"] = self.cache.get_stats()
        report["断路器"] = self.circuit_breaker.get_status()
        return report

    def health_check(self) -> dict:
        """健康检查"""
        return {
            "status": "healthy",
            "agent_id": self.agent_id,
            "model": self.config.model,
            "circuit_breaker": self.circuit_breaker.state,
            "cache_size": len(self.cache._store),
            "success_rate": self.metrics._metrics.success_rate,
        }

    def cleanup(self) -> None:
        """清理资源"""
        self.cache.clear()
        self.metrics.reset()
        self.logger.log_action(self.agent_id, "cleanup", output_data="资源已清理")
        print(f"  🧹 [{self.agent_id}] 资源已清理")


# ==================== 直接测试 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  生产级 Agent 自测")
    print("=" * 60)

    agent = ProductionAgent()
    print(f"✅ Agent 初始化完成: {agent.agent_id}")
    print(f"   模型: {agent.config.model}")
    print(f"   工具: {', '.join(t.name for t in agent.tools)}")

    # 测试单个查询
    print(f"\n  💬 测试查询...")
    try:
        result = agent.execute("搜索关于 AI Agent 的信息")
        print(f"\n  📊 结果: {result}")
    except Exception as e:
        print(f"  ⚠️ LLM 调用失败: {e}")

    # 健康检查
    print(f"\n  🏥 健康检查:")
    for k, v in agent.health_check().items():
        print(f"    {k}: {v}")

    agent.cleanup()
