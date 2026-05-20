# Day 23: Web UI 与部署

> 🎯 **学习目标**
>
> - 用 Streamlit 构建 RAG Agent 对话 Web UI（含检索来源展示）
> - 掌握 AgentService 服务层：会话管理、健康检查、多用户隔离
> - 理解生产环境部署：Docker 容器化、Nginx 反向代理、环境变量管理
> - 掌握生产就绪检查清单：安全、性能、可观测性
> - 完成 24 天 AI 大模型应用开发学习之旅！

---

## 📖 Day 22 回顾

Day 22 我们构建了 RAG + Agent 融合系统：
- ✅ ConversationalRAGAgent — ReAct 循环 + 原生 Function Calling
- ✅ QueryRouter — LLM 驱动的三路分类
- ✅ RAGAgentCache — TTL + LRU 双层缓存
- ✅ RAGRetriever — BM25 + 向量 + RRF 混合检索

**今天，最后一步！** 将融合系统包装为 Web 应用，并学习如何部署到生产环境。

---

## 📚 新知识讲解

### 1. 系统架构总览

```
┌─────────────────────────────────────────────────┐
│                   浏览器                          │
│         http://localhost:8501                    │
└─────────────────┬───────────────────────────────┘
                  │ HTTP/WebSocket
                  ▼
┌─────────────────────────────────────────────────┐
│              Nginx (反向代理)                     │
│         HTTPS · WebSocket · 静态资源缓存          │
└─────────────────┬───────────────────────────────┘
                  │ proxy_pass
                  ▼
┌─────────────────────────────────────────────────┐
│           Streamlit (Web 框架)                   │
│    web_ui.py — 聊天界面 + 来源展示 + 路由可视化    │
└─────────────────┬───────────────────────────────┘
                  │ Python import
                  ▼
┌─────────────────────────────────────────────────┐
│          AgentService (服务层)                    │
│    会话管理 · 健康检查 · 多用户隔离 · 统计         │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│      ConversationalRAGAgent (Day 22 核心)        │
│    ReAct 循环 · 路由分类 · 工具调用 · 缓存        │
└─────────────────────────────────────────────────┘
```

### 2. AgentService 服务层

**为什么需要服务层？**

Day22 的 ConversationalRAGAgent 是单实例的——一个会话对应一个 Agent。但在 Web 应用中，需要管理多个用户、多个会话。AgentService 解决了这个问题。

核心能力：
- **会话管理**：创建/查询/重置/删除会话，每个会话独立的对话历史和 Agent 状态
- **健康检查**：检查服务是否正常运行（uptime、错误率、活跃会话数）
- **自动清理**：过期会话自动回收（默认 1 小时无活跃则删除）
- **资源限制**：max_sessions 参数防止内存溢出

```python
service = AgentService(max_sessions=100)

# 创建会话
session_id = service.create_session()

# 处理查询
response = service.query(session_id, "什么是 RAG？")

# 健康检查
health = service.health_check()
# → {"status": "healthy", "active_sessions": 5, "error_rate": "0.0%"}
```

详见 [agent_service.py](agent_service.py)。

### 3. Streamlit Web UI

**比喻**：Streamlit 就像搭积木——用简单的 Python 代码就能构建出漂亮的 Web 界面。

核心功能：
- **对话界面**：`st.chat_message()` + `st.chat_input()` 实现类 ChatGPT 体验
- **来源展示**：可展开的检索来源面板（source + score + content preview）
- **路由可视化**：彩色标签显示查询分类（rag/direct/tool）
- **侧边栏**：缓存命中率、服务状态、对话统计
- **会话管理**：重置对话、新建会话按钮

关键实现细节：

```python
# 缓存 AgentService 实例（不随页面 rerun 重建）
@st.cache_resource
def get_service():
    return AgentService()

# 初始化会话状态
if "session_id" not in st.session_state:
    st.session_state.session_id = get_service().create_session()
```

启动方式：
```bash
streamlit run web_ui.py
```

详见 [web_ui.py](web_ui.py)。

### 4. 部署方案

#### 方案一：直接运行（开发/测试）
```bash
pip install -r requirements.txt
streamlit run web_ui.py
```

#### 方案二：Docker 部署（推荐）
```bash
docker build -t rag-agent .
docker run -d -p 8501:8501 --env-file .env rag-agent
```

#### 方案三：Docker Compose（多服务编排）
```bash
docker-compose up -d
```

#### Nginx 反向代理（HTTPS + WebSocket）
Streamlit 使用 WebSocket 通信，Nginx 需要特殊配置：
```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
proxy_read_timeout 86400;  # WebSocket 长连接
```

详见 [deployment.py](deployment.py)。

### 5. 生产环境检查清单

| 检查项 | 说明 | 严重性 |
|--------|------|--------|
| API Key 已配置 | 不是默认值 `sk-your-...` | 🔴 必须 |
| DEBUG=false | 关闭调试模式 | 🔴 必须 |
| HTTPS 已启用 | Nginx/Caddy 反向代理 | 🟡 推荐 |
| 日志收集 | ELK/Loki + 结构化日志 | 🟡 推荐 |
| 资源限制 | Docker memory/cpu limits | 🟡 推荐 |
| 监控告警 | Prometheus + Grafana | 🟢 可选 |
| 速率限制 | 防止滥用 | 🟢 可选 |

---

## 💡 实例演示

### 实例 1：启动 Web UI

```bash
cd phase5_capstone/day23_web_ui_deployment
streamlit run web_ui.py
```

浏览器打开 `http://localhost:8501`，即可看到对话界面。

### 实例 2：AgentService 后端调用

```python
from agent_service import AgentService

service = AgentService()
session_id = service.create_session()

# 知识检索型问题
response = service.query(session_id, "什么是 RAG 检索增强生成？")
print(response.answer)

# 多轮对话
response = service.query(session_id, "它的优势是什么？")
print(response.answer)

# 健康检查
print(service.health_check())
```

### 实例 3：生产就绪检查

```python
from deployment import DeploymentConfig

checks = DeploymentConfig.check_production_readiness()
for check, passed in checks.items():
    print(f"{'✅' if passed else '❌'} {check}")
```

**运行方法：**
```bash
cd phase5_capstone/day23_web_ui_deployment
python example.py
```

---

## ✍️ 练习题

### 练习 1：基础题
1. 运行 `python example.py`，观察 5 个演示的输出
2. 启动 Streamlit Web UI：`streamlit run web_ui.py`
3. 在 Web UI 中提问："什么是 RAG？"、"ChromaDB 是什么？"，观察路由标签和来源展示

### 练习 2：进阶题
1. 给 Web UI 添加"导出对话"按钮：将当前对话历史导出为 Markdown 文件
2. 给 AgentService 添加 `list_sessions()` 方法：列出所有活跃会话
3. 添加"对话主题自动命名"：用 LLM 根据第一轮对话生成会话标题

### 练习 3：挑战题
1. 实现"流式输出"：Agent 的回答逐字显示（参考 `stream=True` 的 OpenAI API）
2. 添加"用户反馈"按钮：每条回答的"有用/无用"投票
3. 实现"知识库管理"页面：上传文档、查看索引状态、重建索引

---

## 🎓 24 天课程总回顾

恭喜你完成了全部 24 天的学习！让我们回顾一下这段旅程：

```
Phase 1 (Day 1-5):   Python 基础            — 环境、数据结构、函数、文件IO
Phase 2 (Day 6-10):  LLM 核心能力           — API调用、Context Engineering、Function Calling、Agent基础、MCP协议
Phase 3 (Day 11-15): Agent 深度             — 工具与记忆、高级模式、多Agent协作、编排、生产化
Phase 4 (Day 16-20): RAG 实战               — 向量数据库、文档处理、检索优化、评估、生产化
Phase 5 (Day 21-23): 综合实战               — 项目规划、Agent+RAG融合、Web UI与部署
```

**你掌握的核心能力：**
1. ✅ 原生 openai SDK 调用（零 LangChain 依赖）
2. ✅ Context Engineering（从 prompt 到 context 的思维升级）
3. ✅ ReAct Agent 从零实现（Thought → Action → Observation 循环）
4. ✅ MCP 协议（工具标准化：JSON-RPC + stdio transport）
5. ✅ 混合检索（BM25 + 向量 + RRF 融合 + CrossEncoder 重排序）
6. ✅ Agent + RAG 融合（Agent 调度 RAG，非固定管道）
7. ✅ 生产化基础设施（配置、日志、缓存、重试、断路器、指标）
8. ✅ Web UI 与部署（Streamlit + Docker + Nginx）

---

## 📝 今日总结

- ✅ AgentService — 会话管理 + 多用户隔离 + 健康检查
- ✅ Streamlit Web UI — 聊天界面 + 来源展示 + 路由可视化
- ✅ Docker 部署 — 容器化 + 环境变量注入
- ✅ Nginx 反向代理 — HTTPS + WebSocket 支持
- ✅ 生产检查清单 — 安全 + 性能 + 可观测性
- ✅ 24 天课程完结！🎉

---

## 🚀 下一步

1. 完成所有练习题
2. 用自己的知识库替换 DEMO_DOCUMENTS
3. 部署到云服务器（阿里云/腾讯云/AWS）
4. 持续学习：关注 AI 领域最新进展（模型更新、新协议、新范式）

---

## 📖 参考资料

- [Streamlit Chat Elements](https://docs.streamlit.io/develop/api-reference/chat)
- [Streamlit Session State](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)
- [Docker — Get Started](https://docs.docker.com/get-started/)
- [Nginx WebSocket Proxying](https://nginx.org/en/docs/http/websocket.html)
- [12-Factor App](https://12factor.net/)
- [OpenAI Streaming API](https://platform.openai.com/docs/api-reference/streaming)
