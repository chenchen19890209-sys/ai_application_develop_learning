"""
web_ui.py — Day 23 Streamlit Web UI：RAG Agent 对话界面

功能：
1. 对话界面 — 类 ChatGPT 的聊天 UI
2. 检索来源展示 — 每条回答可展开查看引用来源
3. 路由可视化 — 显示查询被分类到哪条路径
4. 缓存统计 — 侧边栏展示 Agent 运行状态
5. 会话管理 — 新建/重置对话

启动方法：
    streamlit run web_ui.py

设计原则：
- 响应式布局，适配桌面和移动端
- 状态管理通过 st.session_state
- 与 agent_service.py 解耦，可替换后端
"""
import sys
from pathlib import Path

# 配置项目路径
_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root))
_day22_path = Path(__file__).parent.parent / "day22_rag_agent_fusion"
sys.path.insert(0, str(_day22_path))

import streamlit as st
import time
from agent_service import AgentService


# ==================== 页面配置 ====================
st.set_page_config(
    page_title="RAG Agent — 智能客服",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== 样式 ====================
st.markdown("""
<style>
    /* 来源引用样式 */
    .source-box {
        background-color: #f0f2f6;
        border-left: 3px solid #4a90d9;
        padding: 10px 14px;
        margin: 6px 0;
        border-radius: 4px;
        font-size: 0.9em;
    }
    .source-box .score {
        color: #888;
        font-size: 0.8em;
    }
    /* 路由标签样式 */
    .route-tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.75em;
        font-weight: bold;
    }
    .route-rag { background: #e3f2fd; color: #1565c0; }
    .route-direct { background: #e8f5e9; color: #2e7d32; }
    .route-tool { background: #fff3e0; color: #e65100; }
</style>
""", unsafe_allow_html=True)


# ==================== 初始化服务 ====================
@st.cache_resource
def get_service():
    """获取 AgentService 单例（缓存资源，不随 rerun 重建）"""
    return AgentService()


def init_session():
    """初始化 Streamlit 会话状态"""
    if "service" not in st.session_state:
        st.session_state.service = get_service()
    if "session_id" not in st.session_state:
        st.session_state.session_id = st.session_state.service.create_session()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "route_history" not in st.session_state:
        st.session_state.route_history = []


# ==================== 侧边栏 ====================
def render_sidebar():
    """渲染侧边栏 — 状态和控制面板"""
    with st.sidebar:
        st.title("🤖 RAG Agent")
        st.caption("智能客服系统 — Day 23")

        # 会话信息
        st.divider()
        session_info = st.session_state.service.get_session_info(
            st.session_state.session_id
        )
        if session_info:
            st.metric("对话轮数", session_info["query_count"])

        # 缓存统计
        agent_stats = session_info.get("agent_stats", {}) if session_info else {}
        cache_stats = agent_stats.get("cache_stats", {})
        if cache_stats:
            st.metric("缓存命中率", cache_stats.get("hit_rate", "N/A"))

        # 服务状态
        st.divider()
        st.subheader("🖥️ 服务状态")
        health = st.session_state.service.health_check()
        st.text(f"运行时间: {health['uptime_seconds']:.0f}s")
        st.text(f"活跃会话: {health['active_sessions']}")
        st.text(f"总查询: {health['total_queries']}")
        st.text(f"错误率: {health['error_rate']}")

        # 操作按钮
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 重置对话", use_container_width=True):
                st.session_state.service.reset_session(st.session_state.session_id)
                st.session_state.messages = []
                st.session_state.route_history = []
                st.rerun()
        with col2:
            if st.button("🆕 新会话", use_container_width=True):
                st.session_state.session_id = st.session_state.service.create_session()
                st.session_state.messages = []
                st.session_state.route_history = []
                st.rerun()

        # 关于
        st.divider()
        st.caption(
            "基于 **Agent + RAG 融合架构**\n\n"
            "Agent 作为核心调度器，RAG 作为知识检索工具。\n"
            "零 LangChain，纯原生实现。"
        )


# ==================== 消息渲染 ====================
def render_message(msg: dict):
    """渲染单条消息

    Args:
        msg: 消息字典 {role, content, sources, route, time_ms}
    """
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # 显示路由标签
        if msg.get("route"):
            route = msg["route"]
            emoji = {"rag": "📚", "direct": "💬", "tool": "🔧"}.get(route, "")
            st.markdown(
                f'<span class="route-tag route-{route}">{emoji} {route}</span>',
                unsafe_allow_html=True,
            )

        # 显示检索来源
        if msg.get("sources"):
            with st.expander("📚 查看检索来源"):
                for i, src in enumerate(msg["sources"], 1):
                    score_pct = f"{src.get('score', 0):.1%}" if isinstance(src.get('score'), float) else ""
                    st.markdown(
                        f'<div class="source-box">'
                        f'<strong>[{i}]</strong> {src.get("source", "未知")} '
                        f'<span class="score">{score_pct}</span>'
                        f'<br>{src.get("content", "")[:200]}...'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        # 显示耗时
        if msg.get("time_ms"):
            st.caption(f"⏱️ {msg['time_ms']:.0f}ms · {msg.get('steps', 0)} 步")


# ==================== 主界面 ====================
def main():
    """主函数 — Streamlit 应用入口"""
    init_session()
    render_sidebar()

    # 标题
    st.title("🤖 RAG Agent 智能客服")
    st.caption("基于 Agent + RAG 融合架构 · 知识库问答系统")

    # 显示已有消息
    for msg in st.session_state.messages:
        render_message(msg)

    # 用户输入
    if prompt := st.chat_input("请输入您的问题..."):
        # 显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 调用 Agent
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                start = time.time()
                try:
                    response = st.session_state.service.query(
                        st.session_state.session_id, prompt
                    )
                    elapsed = (time.time() - start) * 1000

                    # 渲染回答
                    st.markdown(response.answer)

                    # 提取路由信息（从 Agent 的 action 中推断）
                    route = "rag" if any(
                        a.tool_name == "search_knowledge" for a in response.actions
                    ) else "direct"

                    # 显示路由标签
                    emoji = {"rag": "📚", "direct": "💬", "tool": "🔧"}.get(route, "")
                    st.markdown(
                        f'<span class="route-tag route-{route}">{emoji} {route}</span>',
                        unsafe_allow_html=True,
                    )

                    # 显示来源（从 action 的 tool_output 提取）
                    if response.sources:
                        with st.expander("📚 查看检索来源"):
                            for i, src in enumerate(response.sources, 1):
                                st.markdown(
                                    f'<div class="source-box">'
                                    f'<strong>[{i}]</strong> {src.source} '
                                    f'<span class="score">{src.score:.1%}</span>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )

                    st.caption(
                        f"⏱️ {elapsed:.0f}ms · {response.total_steps} 步 · "
                        f"路由: {route}"
                    )

                    # 保存消息到历史
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.answer,
                        "route": route,
                        "sources": [
                            {"source": s.source, "content": s.content, "score": s.score}
                            for s in response.sources
                        ],
                        "time_ms": elapsed,
                        "steps": response.total_steps,
                    })

                except Exception as e:
                    st.error(f"处理出错: {e}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"抱歉，处理您的请求时出错: {e}",
                        "route": "direct",
                    })


if __name__ == "__main__":
    main()
