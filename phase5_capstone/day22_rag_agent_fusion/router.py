"""
router.py — Day 22 查询路由模块

QueryRouter 使用 LLM 对用户查询进行分类，决定处理路径：
- "rag" → 需要知识库检索（如"什么是 RAG？"）
- "direct" → 可直接回答（如"你好，今天天气怎么样？"）
- "tool" → 需要调用其他工具（如"帮我算一下 123*456"）

路由分类结果决定 Agent 后续的行为路径，避免不必要的检索开销。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

import json
from typing import Optional, Dict, Any
from openai import OpenAI


class QueryRouter:
    """查询路由器 — LLM 驱动的意图分类

    工作原理：
    1. 接收用户查询文本
    2. 调用 LLM（轻量 prompt + json_object 模式）进行分类
    3. 返回路由决策（rag / direct / tool）+ 置信度

    优势：比关键词匹配更智能，能理解隐含意图。
    例如"最近 AI 有什么新进展"应该路由到 RAG，尽管没有明确的"搜索"关键词。
    """

    # 路由决策的 JSON Schema（用于 json_object 模式的 prompt 指导）
    ROUTE_SCHEMA = {
        "route": "rag|direct|tool",
        "reason": "分类理由",
        "confidence": 0.9,
        "suggested_tools": ["工具名（仅 tool 路由时填充）"]
    }

    def __init__(self):
        """初始化路由器 — 创建 LLM 客户端"""
        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

    def classify(self, query: str) -> Dict[str, Any]:
        """对用户查询进行分类，返回路由决策

        Args:
            query: 用户输入的自然语言查询

        Returns:
            路由决策字典:
            {
                "route": "rag" | "direct" | "tool",
                "reason": "分类理由",
                "confidence": 0.0-1.0
            }
        """
        prompt = f"""你是一个查询路由器。请分析用户查询，判断应该走哪条处理路径。

查询：「{query}」

路径说明：
1. **rag** — 需要从知识库检索信息才能回答的问题。
   特征：询问概念、定义、原理、技术细节、事实性知识。
   例如："什么是 RAG？"、"ChromaDB 怎么用？"、"BM25 和向量检索有什么区别？"

2. **direct** — 可以直接用 LLM 自身知识回答，不需要检索。
   特征：闲聊、简单常识、主观意见、基础计算。
   例如："你好！"、"今天心情不错"、"Python 是什么？"

3. **tool** — 需要调用外部工具（计算器、天气查询、数据库查询等），
   且不需要知识库检索。
   例如："帮我算 123 * 456"、"现在北京天气怎么样？"

请以 JSON 格式返回：{{"route": "...", "reason": "...", "confidence": 0.9}}"""

        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=200,
        )

        raw = response.choices[0].message.content
        result = json.loads(raw)

        # 标准化路由值
        route = result.get("route", "direct")
        if route not in ("rag", "direct", "tool"):
            route = "direct"

        return {
            "route": route,
            "reason": result.get("reason", ""),
            "confidence": result.get("confidence", 0.5),
        }
