"""
agent_service.py — Day 23 后端服务：将 RAG Agent 封装为可调用的服务

提供 AgentService 类，作为 Day22 ConversationalRAGAgent 的服务层封装：
- 单例模式管理 Agent 实例
- 会话管理（多用户、多会话）
- 健康检查端点
- 统计信息查询

设计原则：与 Web UI 解耦，可独立测试和部署。
"""
import sys
from pathlib import Path

# 导入 Day22 的 Agent（父级目录的 day22）
_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root))

# Day22 模块路径
_day22_path = Path(__file__).parent.parent / "day22_rag_agent_fusion"
sys.path.insert(0, str(_day22_path))

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from agent import ConversationalRAGAgent
from models import AgentResponse

import uuid
import time
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Session:
    """用户会话 — 每个用户/每次对话的状态管理"""
    session_id: str                              # 会话唯一 ID
    agent: ConversationalRAGAgent                # Agent 实例
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    query_count: int = 0


class AgentService:
    """Agent 服务层 — 管理 Agent 实例和会话

    职责：
    1. Agent 生命周期管理（创建、复用、销毁）
    2. 会话隔离（每个 session 独立的对话历史）
    3. 健康检查和统计

    生产环境中可扩展为：
    - 连接池管理（多 Agent 实例）
    - 会话持久化（Redis）
    - 请求队列和限流
    """

    def __init__(self, max_sessions: int = 100):
        """初始化服务

        Args:
            max_sessions: 最大会话数
        """
        self.max_sessions = max_sessions
        self._sessions: Dict[str, Session] = {}

        # 统计信息
        self.total_queries = 0
        self.total_errors = 0
        self.start_time = time.time()

    def create_session(self) -> str:
        """创建新会话 — 返回 session_id

        Returns:
            新会话的唯一 ID
        """
        # 清理过期会话（超过 1 小时未活跃）
        self._cleanup_expired()

        # 限制会话数
        if len(self._sessions) >= self.max_sessions:
            # 删除最旧的会话
            oldest = min(self._sessions.keys(),
                        key=lambda k: self._sessions[k].last_active)
            del self._sessions[oldest]

        session_id = str(uuid.uuid4())[:8]
        agent = ConversationalRAGAgent()
        agent.verbose = False  # 生产模式不打印调试信息

        self._sessions[session_id] = Session(
            session_id=session_id,
            agent=agent,
        )
        return session_id

    def query(self, session_id: str, user_query: str) -> AgentResponse:
        """处理用户查询

        Args:
            session_id: 会话 ID
            user_query: 用户输入

        Returns:
            AgentResponse（含答案、步骤、来源）
        """
        if session_id not in self._sessions:
            raise ValueError(f"会话不存在: {session_id}")

        session = self._sessions[session_id]
        session.last_active = time.time()
        session.query_count += 1
        self.total_queries += 1

        try:
            response = session.agent.run(user_query)
            return response
        except Exception as e:
            self.total_errors += 1
            raise

    def reset_session(self, session_id: str):
        """重置会话 — 清空对话历史但保留 Agent 实例

        Args:
            session_id: 会话 ID
        """
        if session_id in self._sessions:
            self._sessions[session_id].agent.reset_conversation()

    def delete_session(self, session_id: str):
        """删除会话

        Args:
            session_id: 会话 ID
        """
        if session_id in self._sessions:
            del self._sessions[session_id]

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """获取会话信息

        Args:
            session_id: 会话 ID

        Returns:
            会话统计信息字典
        """
        if session_id not in self._sessions:
            return None

        session = self._sessions[session_id]
        return {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "last_active": session.last_active,
            "query_count": session.query_count,
            "agent_stats": session.agent.stats,
        }

    def health_check(self) -> Dict:
        """健康检查 — 返回服务状态

        Returns:
            服务健康状态字典
        """
        return {
            "status": "healthy",
            "uptime_seconds": time.time() - self.start_time,
            "active_sessions": len(self._sessions),
            "total_queries": self.total_queries,
            "total_errors": self.total_errors,
            "error_rate": f"{self.total_errors / max(self.total_queries, 1):.1%}",
        }

    def _cleanup_expired(self, max_idle_seconds: float = 3600):
        """清理过期会话（超过指定时间未活跃）

        Args:
            max_idle_seconds: 最大空闲时间（秒），默认 1 小时
        """
        now = time.time()
        expired = [
            sid for sid, sess in self._sessions.items()
            if now - sess.last_active > max_idle_seconds
        ]
        for sid in expired:
            del self._sessions[sid]
