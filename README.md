# AI 大模型应用开发学习教程

> 23 天从零掌握 AI 应用开发 — **零 LangChain，纯原生实现**

## 课程概览

本教程是一套系统的 AI 大模型应用开发学习路径，涵盖 5 个阶段、23 天。从 Python 基础开始，逐步深入到 LLM API 调用、Context Engineering、Agent 系统、MCP 协议、RAG 检索增强生成，最终完成一个完整的 Agent + RAG 融合项目。

**核心理念**：协议优先于框架。用原生 `openai` SDK 和 MCP 协议替代 LangChain 封装，让学生理解底层原理而非框架 API。

## 课程结构

```
Phase 1 (5天)    Python 基础           环境配置、控制流、数据结构、函数模块、文件IO
Phase 2 (5天)    LLM 核心能力           API调用、Context Engineering、Function Calling、
                                       Agent基础、MCP协议
Phase 3 (5天)    Agent 深度            自定义工具与记忆、高级Agent模式、多Agent协作、
                                       Agent编排、Agent生产化
Phase 4 (5天)    RAG 实战              向量数据库、文档处理、混合检索、RAG评估、
                                       生产级RAG
Phase 5 (3天)    综合实战              项目规划、Agent+RAG融合、Web UI与部署
```

| 天 | 主题 | 关键内容 |
|----|------|---------|
| 01 | Python 环境配置 | venv、pip、VSCode、.env 管理 |
| 02 | 控制流程 | 条件、循环、函数基础 |
| 03 | 数据结构 | list/dict/set/tuple + 推导式 |
| 04 | 函数与模块 | 装饰器、生成器、import 机制 |
| 05 | 文件与异常 | 文件IO、异常处理、numpy/pandas 基础 |
| 06 | LLM 基础 | OpenAI SDK、Token、模型选型 |
| 07 | Context Engineering | 系统消息设计、工具描述、记忆管理 |
| 08 | Function Calling | JSON Schema 定义、多函数调用 |
| 09 | Agent 基础 | ReAct 模式从零实现、tool-calling loop |
| 10 | MCP 协议 | MCP Server/Client、JSON-RPC、工具标准化 |
| 11 | 自定义工具与记忆 | 生产级工具、三级记忆系统 |
| 12 | 高级 Agent 模式 | Plan-Execute、ReWOO、Self-Ask |
| 13 | 多 Agent 协作 | 顺序/并行/投票/Manager-Worker |
| 14 | Agent 编排 | 工作流编排、条件路由、管道 |
| 15 | Agent 生产化 | 重试、限流、断路器、指标、安全 |
| 16 | RAG 原理与向量库 | RAG 架构、Embedding、ChromaDB |
| 17 | 文档处理 | 分块策略、文档加载、RAG 构建 |
| 18 | 检索优化 | BM25+向量混合检索、RRF 融合、重排序 |
| 19 | RAG 评估 | Faithfulness/Relevance、Precision@K/NDCG |
| 20 | 生产级 RAG | 配置/日志/缓存/重试/混合检索 |
| 21 | 项目规划 | 需求分析、技术选型、架构设计、风险评估 |
| 22 | Agent + RAG 融合 | Agent 调度 RAG、路由分类、缓存、多轮对话 |
| 23 | Web UI 与部署 | Streamlit、Docker、Nginx、生产检查清单 |

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/chenchen19890209-sys/ai_application_develop_learning.git
cd ai_application_develop_learning

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 配置 API Key
cp .env.example .env
# 编辑 .env 填入你的 OPENAI_API_KEY
```

### 2. 按天学习

```bash
# 安装当天依赖
pip install -r phase2_llm_core/day06_llm_basics/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 运行当天示例
python phase2_llm_core/day06_llm_basics/first_llm_call.py
```

### 3. 启动 Web UI（Day 23）

```bash
streamlit run phase5_capstone/day23_web_ui_deployment/web_ui.py
```

## 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| LLM SDK | `openai` (原生 SDK) | 兼容 OpenAI / DeepSeek / 任何 OpenAI-compatible API |
| 协议 | MCP (JSON-RPC 2.0) | 工具标准化通信协议 |
| 向量数据库 | ChromaDB (原生 SDK) | 嵌入式向量数据库 |
| 嵌入模型 | BAAI/bge-small-zh-v1.5 | 中文语义嵌入 |
| 检索算法 | BM25 + RRF + CrossEncoder | 混合检索 + 重排序 |
| Web UI | Streamlit | 对话界面 + 来源展示 |
| 部署 | Docker + Nginx | 容器化 + HTTPS 反向代理 |

## 关键设计原则

1. **协议优于框架** — 用原生 `openai` SDK 和 MCP 协议，不用 LangChain
2. **Context 优于 Prompt** — Day 7 起教 Context Engineering 而非手写 prompt 咒语
3. **Agent 优先于 RAG** — Agent 是核心范式，RAG 是 Agent 的检索工具
4. **精简 RAG** — 5 天覆盖生产实际需要，舍弃学术性变体
5. **MCP 作为基础设施** — Day 10 即引入，非事后补充
6. **干中学** — 每个阶段末尾有迷你项目，Day 21-23 完整实战

## 仓库结构

```
ai_develop_learning_claude/
├── README.md                    # 本文件
├── CLAUDE.md                    # Claude Code 项目指引
├── config.py                    # 共享配置（所有天复用）
├── .env.example                 # 环境变量模板
├── phase1_fundamentals/         # 5 天 Python 基础
├── phase2_llm_core/             # 5 天 LLM 核心
├── phase3_agent/                # 5 天 Agent 深度
├── phase4_rag/                  # 5 天 RAG 实战
└── phase5_capstone/             # 3 天综合实战
```

每天目录包含 `tutorial.md`（教程）+ Python 代码 + `requirements.txt`。

## 编程要求

- Python 3.11+
- 所有 API Key 通过 `.env` 环境变量管理，绝不硬编码
- 代码全部原生实现，零 LangChain 依赖
- 每行代码包含详细中文注释

## 许可

MIT License
