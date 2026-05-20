"""
agent.py — Day 22 核心：RAG + Agent 融合系统

ConversationalRAGAgent 将 Phase 3 的 Agent 架构与 Phase 4 的 RAG 检索融合：
- Agent 作为核心调度器 → 工具调用循环（ReAct）
- RAG 作为知识检索工具 → 为 LLM 提供最新/私有知识
- 路由器 → 智能判断是否需要检索
- 缓存 → 避免重复检索

整个系统零 LangChain 依赖，100% 原生 openai SDK + Python。

架构流程：
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ User Input  │ →   │ QueryRouter  │ →   │   Agent     │
└─────────────┘     └──────────────┘     │  (ReAct)    │
       │                  │               └──────┬──────┘
       │            ┌─────┼─────┐               │
       │            ↓     ↓     ↓               ↓
       │          RAG  Direct  Tool      ┌─────────────┐
       │          path  path   path      │  LLM 推理   │
       │            ↓                    │  + 工具调用  │
       │     ┌─────────────┐            └──────┬──────┘
       │     │ RAGRetriever│                   │
       │     │  + Cache    │                   ↓
       │     └─────────────┘            ┌─────────────┐
       │            │                   │  最终回复    │
       │            ↓                   └─────────────┘
       │     ┌─────────────┐
       └──→  │ AgentResponse│
             └─────────────┘
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

import json
import time
from typing import List, Optional, Dict, Any
from openai import OpenAI

from models import RAGResult, ChatMessage, AgentAction, AgentResponse
from retriever import RAGRetriever
from router import QueryRouter
from cache import RAGAgentCache


class ConversationalRAGAgent:
    """对话式 RAG Agent — RAG + Agent 融合的核心实现

    工作流程：
    1. 接收用户查询 → QueryRouter 分类
    2. 根据分类结果决定工具集：
       - rag 路径：加载 RAG 检索工具 + 通用工具
       - direct 路径：不加载工具，直接对话
       - tool 路径：加载计算器/天气等通用工具
    3. ReAct 循环：LLM 推理 → 决定调用工具 → 执行工具 → 观察结果
    4. 生成最终回复（含检索来源引用）

    核心设计决策：
    - RAG 检索是 Agent 的一个工具（而不是固定前置步骤）
    - Agent 自己决定是否需要检索、检索什么、用几次
    - 这比"先检索再回答"的固定管道更灵活
    """

    def __init__(self, system_prompt: str = None):
        """初始化 RAG Agent

        Args:
            system_prompt: 自定义系统提示（可选）
        """
        # LLM 客户端（原生 openai SDK）
        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

        # 核心组件
        self.router = QueryRouter()            # 查询路由器
        self.retriever = RAGRetriever()        # RAG 检索器
        self.cache = RAGAgentCache()           # 检索缓存

        # 确保检索器已索引
        self.retriever.index()

        # 对话历史
        self.conversation_history: List[Dict[str, Any]] = []

        # 系统提示
        self.system_prompt = system_prompt or self._default_system_prompt()

        # Agent 配置
        self.max_iterations = 8   # 最大工具调用轮数
        self.verbose = True       # 是否打印详细过程

        # 统计信息
        self.total_queries = 0
        self.cache_hits = 0

    def _default_system_prompt(self) -> str:
        """默认系统提示 — 指导 Agent 的行为模式"""
        return """你是一个智能客服助手，拥有知识库检索能力。

## 工作原则
1. 分析用户问题，判断是否需要从知识库检索信息
2. 如果问题涉及技术概念、原理、操作指南，使用 search_knowledge 工具检索
3. 基于检索结果生成准确、有引用的回答
4. 如果检索结果不足以回答问题，诚实告知并建议用户提供更多信息
5. 如果问题是闲聊或常识，直接友好回复
6. 回复中尽量引用知识库来源（标注 [来源: xxx]）
7. 保持回复自然、友好、专业

## 工具使用指南
- search_knowledge: 检索内部知识库，获取技术文档和概念解释
- calculate: 执行数学计算

## 回复格式
- 基于知识库的回答：先给出答案，再标注来源
- 直接回答（无需检索）：简洁明了
- 无法回答时：诚实说明 + 建议"""

    # ==================== 工具定义（MCP 兼容格式）====================

    def _get_rag_tool(self) -> Dict[str, Any]:
        """RAG 检索工具定义 — JSON Schema 格式"""
        return {
            "type": "function",
            "function": {
                "name": "search_knowledge",
                "description": "搜索内部知识库，获取技术概念、原理、操作指南等信息。适合回答需要专业知识的提问。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询文本，应提取用户问题的核心关键词"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返回的结果数量，默认 3",
                            "default": 3
                        }
                    },
                    "required": ["query"]
                }
            }
        }

    def _get_calculator_tool(self) -> Dict[str, Any]:
        """计算器工具定义"""
        return {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "执行安全的数学计算，支持加减乘除、括号、小数",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "数学表达式，如 '123 * 456'、'(1+2)*3'"
                        }
                    },
                    "required": ["expression"]
                }
            }
        }

    # ==================== 工具执行器 ====================

    def _execute_search_knowledge(self, query: str, top_k: int = 3) -> str:
        """执行知识库检索 — 先查缓存，未命中再检索

        Args:
            query: 搜索查询
            top_k: 返回结果数

        Returns:
            格式化的检索结果文本
        """
        # 先查缓存
        cached = self.cache.get(query)
        if cached:
            self.cache_hits += 1
            if self.verbose:
                print(f"    💾 缓存命中! (命中率:{self.cache.stats['hit_rate']})")
            return self.retriever.format_for_llm(cached)

        # 执行混合检索
        results = self.retriever.search(query, top_k=top_k, use_hybrid=True)

        # 存入缓存
        self.cache.set(query, results)

        return self.retriever.format_for_llm(results)

    def _execute_calculate(self, expression: str) -> str:
        """安全执行数学计算

        Args:
            expression: 数学表达式

        Returns:
            计算结果文本
        """
        # 安全校验：只允许数字和算术符号
        allowed = set("0123456789+-*/.()% eEpPiI")
        if not all(c in allowed for c in expression.replace(" ", "")):
            return "错误：表达式包含不允许的字符。"
        try:
            result = eval(expression, {"__builtins__": {}}, {"e": 2.718, "pi": 3.1416})
            return f"{expression} = {result}"
        except Exception as e:
            return f"计算失败：{e}"

    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """工具执行分发器

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            工具执行结果文本
        """
        if tool_name == "search_knowledge":
            return self._execute_search_knowledge(
                query=tool_args.get("query", ""),
                top_k=tool_args.get("top_k", 3),
            )
        elif tool_name == "calculate":
            return self._execute_calculate(
                expression=tool_args.get("expression", ""),
            )
        else:
            return f"未知工具: {tool_name}"

    # ==================== 核心 ReAct 循环 ====================

    def run(self, user_query: str) -> AgentResponse:
        """运行 Agent 处理用户查询

        完整的 ReAct 循环：
        1. 路由分类 → 决定工具集
        2. 构建消息列表（系统提示 + 对话历史 + 用户输入）
        3. LLM 推理 → 判断是否调用工具
        4. 如需调用 → 执行工具 → 记录结果 → 回到步骤 3
        5. 无需调用 → 生成最终回复

        Args:
            user_query: 用户输入的自然语言查询

        Returns:
            AgentResponse（含最终答案、中间步骤、来源引用）
        """
        start_time = time.time()
        self.total_queries += 1

        # 阶段 1：路由分类
        route = self.router.classify(user_query)
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"  🤖 RAG Agent — 处理查询")
            print(f"{'='*60}")
            print(f"  📝 用户: {user_query}")
            print(f"  🔀 路由: {route['route']} (置信度:{route['confidence']:.0%})")
            print(f"     理由: {route['reason']}")

        # 阶段 2：根据路由决定工具集
        tools = []
        if route["route"] == "rag":
            tools.append(self._get_rag_tool())
        elif route["route"] == "tool":
            tools.append(self._get_calculator_tool())
        # direct 路径不加载任何工具

        # 阶段 3：构建消息列表
        messages = self._build_messages(user_query)
        openai_tools = tools if tools else None

        # 阶段 4：ReAct 循环
        actions: List[AgentAction] = []
        sources: List[RAGResult] = []

        for iteration in range(1, self.max_iterations + 1):
            if self.verbose:
                print(f"\n  --- Step {iteration} ---")

            # LLM 推理（REAL API 调用）
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=openai_tools,
                tool_choice="auto" if openai_tools else None,
                temperature=0.3,
            )

            message = response.choices[0].message

            # 检查是否需要调用工具
            if not message.tool_calls:
                # 最终回复
                final_answer = message.content or "处理完成"
                if self.verbose:
                    print(f"  💭 最终回复: {final_answer[:100]}...")

                actions.append(AgentAction(
                    step=iteration,
                    thought="生成最终回复",
                    is_final=True,
                ))

                # 更新对话历史
                self.conversation_history.append({"role": "user", "content": user_query})
                self.conversation_history.append({"role": "assistant", "content": final_answer})

                total_time = (time.time() - start_time) * 1000
                return AgentResponse(
                    answer=final_answer,
                    actions=actions,
                    sources=sources,
                    total_steps=iteration,
                    total_time_ms=total_time,
                    conversation_id=f"conv_{self.total_queries}",
                )

            # 处理工具调用
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                if self.verbose:
                    print(f"  🔧 调用工具: {tool_name}({tool_args})")

                # 执行工具
                tool_output = self._execute_tool(tool_name, tool_args)

                if self.verbose:
                    output_preview = tool_output[:100].replace("\n", " ")
                    print(f"  📋 工具输出: {output_preview}...")

                # 记录动作
                actions.append(AgentAction(
                    step=iteration,
                    thought=f"需要调用 {tool_name} 获取信息",
                    tool_name=tool_name,
                    tool_input=tool_args,
                    tool_output=tool_output,
                ))

                # 将工具调用和结果加入消息列表
                messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": tool_call.function.arguments,
                            }
                        }
                    ]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output,
                })

        # 超过最大迭代次数 — 强制结束
        final_answer = "抱歉，处理超时。请简化您的问题后重试。"
        if self.verbose:
            print(f"  ⚠️ 达到最大迭代次数 {self.max_iterations}")

        total_time = (time.time() - start_time) * 1000
        return AgentResponse(
            answer=final_answer,
            actions=actions,
            sources=sources,
            total_steps=self.max_iterations,
            total_time_ms=total_time,
        )

    def _build_messages(self, user_query: str) -> List[Dict[str, Any]]:
        """构建 LLM 消息列表

        消息结构：系统提示 → 对话历史（最近6轮） → 当前用户输入

        Args:
            user_query: 当前用户输入

        Returns:
            完整的消息列表
        """
        messages = [{"role": "system", "content": self.system_prompt}]

        # 添加最近6轮对话历史（12条消息）
        recent_history = self.conversation_history[-12:] if self.conversation_history else []
        messages.extend(recent_history)

        # 添加当前用户输入
        messages.append({"role": "user", "content": user_query})
        return messages

    # ==================== 多轮对话管理 ====================

    def chat(self, user_query: str) -> str:
        """简化的对话接口 — 只返回答案文本

        Args:
            user_query: 用户输入

        Returns:
            Agent 的回答文本
        """
        response = self.run(user_query)
        return response.answer

    def reset_conversation(self):
        """重置对话历史（开始新会话）"""
        self.conversation_history.clear()
        if self.verbose:
            print("  🔄 对话历史已重置")

    # ==================== 状态查询 ====================

    @property
    def stats(self) -> Dict[str, Any]:
        """Agent 运行统计"""
        return {
            "total_queries": self.total_queries,
            "conversation_turns": len(self.conversation_history) // 2,
            "cache_stats": self.cache.stats,
            "retriever_stats": self.retriever.stats,
        }
