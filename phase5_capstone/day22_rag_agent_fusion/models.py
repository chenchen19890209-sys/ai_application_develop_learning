"""
models.py — Day 22 数据模型：RAG + Agent 融合系统的核心数据结构

定义：
- RAGResult: RAG 检索的单条结果
- ChatMessage: 对话消息（支持多轮）
- AgentAction: Agent 执行的单步动作
- AgentResponse: Agent 最终回复（含检索来源）
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class RAGResult:
    """RAG 检索结果 — 单条检索到的文档片段

    包含原始文本、来源元数据、相关性分数，方便 Agent 判断是否采信。
    """
    content: str                                  # 文档片段内容
    source: str = ""                              # 来源标识（文件名/URL）
    score: float = 0.0                            # 相关性分数（0-1）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据（页码、章节等）


@dataclass
class ChatMessage:
    """对话消息 — 多轮对话的基本单元"""
    role: str                                     # 角色：user / assistant / system / tool
    content: str                                  # 消息内容
    tool_name: Optional[str] = None               # 工具名称（tool 角色时使用）
    tool_call_id: Optional[str] = None            # 工具调用 ID
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentAction:
    """Agent 动作 — ReAct 循环中的单步操作

    记录 Agent 每一步的思考（thought）和行动（action），
    便于调试、日志记录和用户可视化。
    """
    step: int                                     # 步骤编号
    thought: str                                  # 推理过程（思考）
    tool_name: str = ""                           # 调用的工具名称
    tool_input: Dict[str, Any] = field(default_factory=dict)  # 工具输入参数
    tool_output: str = ""                         # 工具返回结果
    is_final: bool = False                        # 是否为最终步骤


@dataclass
class AgentResponse:
    """Agent 回复 — 完整的 Agent 执行结果

    包含最终答案、所有中间步骤、引用的来源，方便前端渲染。
    """
    answer: str                                   # 最终回答文本
    actions: List[AgentAction] = field(default_factory=list)  # ReAct 中间步骤
    sources: List[RAGResult] = field(default_factory=list)    # 引用的检索来源
    total_steps: int = 0                          # 总步数
    total_time_ms: float = 0.0                    # 总耗时（毫秒）
    conversation_id: str = ""                     # 对话 ID（多轮关联）
