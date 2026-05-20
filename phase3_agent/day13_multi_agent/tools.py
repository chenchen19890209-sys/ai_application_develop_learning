"""
tools.py — 多 Agent 协作共享工具集

功能：
1. WebSearchTool — 知识库搜索工具（20+ 条目）
2. CodeAnalysisTool — 代码分析工具（统计行数、函数、复杂度）
3. DataAnalysisTool — 数据分析工具（均值、中位数、最值）
4. ReportTool — 报告格式化工具
5. get_agent_tools() — 按名获取工具子集

设计原则：零 LangChain 依赖、MCP 兼容格式、纯 Python 类
"""


class WebSearchTool:
    """知识库搜索工具 — 模拟多领域搜索"""

    def __init__(self):
        self.name = "search"
        self.description = "搜索知识库，获取科技、科学、历史、地理等领域的权威信息"
        self.inputSchema = {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"}
            },
            "required": ["query"]
        }
        self._kb = {
            "python": "Python 由 Guido van Rossum 于 1991 年创建。2024 年 TIOBE 指数排名第一。广泛应用于 AI、数据科学、Web 后端开发。",
            "深度学习": "深度学习是机器学习的子领域。2012 年 AlexNet 赢得 ImageNet 竞赛标志着深度学习革命的开始。核心架构：CNN、RNN、Transformer。",
            "ai": "人工智能（AI）是计算机科学的分支，目标是创造能执行需要人类智能的任务的系统。2022 年底 ChatGPT 发布后 AI 进入大众视野。",
            "北京": "北京是中华人民共和国首都，位于华北平原，人口约 2189 万。拥有 3000 多年建城史和 800 多年建都史。",
            "气候变化": "全球变暖主要由温室气体排放引起。2015 年《巴黎协定》设定目标：将升温控制在 2°C 以内。2023 年是有记录以来最热的一年。",
            "量子": "量子力学是描述微观粒子行为的物理学理论。量子计算机利用叠加和纠缠原理，理论计算能力远超经典计算机。",
            "http": "HTTP（超文本传输协议）是万维网的基础协议。HTTP/3 基于 QUIC 协议，提供更快的连接建立和更好的移动网络性能。",
            "ssl": "SSL/TLS 是加密通信协议，保证网络数据传输的安全性。TLS 1.3 简化了握手过程，提高了安全性和性能。",
            "docker": "Docker 是容器化平台，允许将应用及其依赖打包成轻量级容器。它简化了开发、测试和生产环境的一致性。",
            "rest": "REST（表述性状态转移）是一种 Web 服务架构风格。它使用 HTTP 方法（GET/POST/PUT/DELETE）操作资源，以 JSON 作为主要数据格式。",
            "sql": "SQL（结构化查询语言）是关系数据库的标准查询语言。核心操作：SELECT（查询）、INSERT（插入）、UPDATE（更新）、DELETE（删除）。",
            "react": "React 由 Facebook 于 2013 年发布，是最流行的前端 JavaScript 框架之一。它使用虚拟 DOM 和组件化架构来构建用户界面。",
            "machine learning": "机器学习通过算法让计算机从数据中学习。三大范式：监督学习（有标签）、无监督学习（无标签）、强化学习（奖励驱动）。",
            "neural network": "神经网络受生物神经系统启发。深度神经网络包含多个隐藏层，通过反向传播算法进行训练。",
            "gpu": "GPU 最初设计用于图形处理，但因其大规模并行计算能力成为深度学习训练的标准硬件。NVIDIA 主导 AI 加速器市场。",
            "token": "在 NLP 中，Token 是文本的基本处理单元。GPT-4 的上下文窗口达 128K tokens。Token 数量影响 API 调用成本和响应速度。",
            "mcp": "MCP（Model Context Protocol）定义 AI 模型与外部工具的标准化通信协议，基于 JSON-RPC 2.0。它实现了工具的跨框架复用。",
            "agent": "AI Agent 是能自主感知、决策和行动的智能系统。核心模式：ReAct、Plan-Execute、ReWOO、Self-Ask。",
            "embedding": "文本 Embedding 将文字转换为高维向量。语义相似的文本其向量距离相近。ChromaDB 是常用的向量存储和检索数据库。",
            "langchain": "LangChain 是 Python LLM 应用框架，提供 Chains、Agents、Tools 抽象。但随着 MCP 协议推广，行业趋向框架无关的工具标准化。",
        }

    def execute(self, query: str) -> dict:
        query_lower = query.lower()
        matches = []
        for keyword, content in self._kb.items():
            if keyword.lower() in query_lower or any(w in query_lower for w in keyword.lower().split()):
                matches.append(f"【{keyword}】{content}")
        if not matches:
            return {"content": [{"type": "text", "text": f"未找到与'{query}'相关的信息。"}]}
        return {"content": [{"type": "text", "text": "\n\n".join(matches)}]}


class CodeAnalysisTool:
    """代码分析工具 — 静态分析代码特征"""

    def __init__(self):
        self.name = "code_analysis"
        self.description = "分析代码片段，统计行数、函数数、类数，评估复杂度"
        self.inputSchema = {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "要分析的源代码"}
            },
            "required": ["code"]
        }

    def execute(self, code: str) -> dict:
        import re
        lines = code.strip().split("\n")
        total_lines = len(lines)
        blank_lines = sum(1 for l in lines if not l.strip())
        comment_lines = sum(1 for l in lines if l.strip().startswith("#") or l.strip().startswith("//"))
        code_lines = total_lines - blank_lines - comment_lines
        functions = len(re.findall(r"def \w+", code))
        classes = len(re.findall(r"class \w+", code))
        imports = len(re.findall(r"^\s*(import|from)\s", code, re.MULTILINE))

        # 圈复杂度简易估算（基于分支关键字）
        branches = len(re.findall(r"\b(if|elif|for|while|and|or)\b", code))
        complexity = "低" if branches < 5 else ("中" if branches < 15 else "高")

        result = (
            f"代码分析结果：\n"
            f"  总行数: {total_lines}（代码 {code_lines} / 注释 {comment_lines} / 空行 {blank_lines}）\n"
            f"  函数: {functions} 个\n"
            f"  类: {classes} 个\n"
            f"  导入: {imports} 条\n"
            f"  分支数: {branches} → 复杂度: {complexity}"
        )
        return {"content": [{"type": "text", "text": result}]}


class DataAnalysisTool:
    """数据分析工具 — 基本统计计算"""

    def __init__(self):
        self.name = "data_analysis"
        self.description = "对数字列表进行统计分析：均值、中位数、最大最小值、标准差"
        self.inputSchema = {
            "type": "object",
            "properties": {
                "numbers": {
                    "type": "string",
                    "description": "逗号分隔的数字，例如 '1,2,3,4,5'"
                }
            },
            "required": ["numbers"]
        }

    def execute(self, numbers: str) -> dict:
        try:
            nums = [float(x.strip()) for x in numbers.split(",") if x.strip()]
        except ValueError:
            return {"content": [{"type": "text", "text": "数据格式错误，请提供逗号分隔的数字"}], "isError": True}
        if not nums:
            return {"content": [{"type": "text", "text": "数据为空"}], "isError": True}

        n = len(nums)
        mean = sum(nums) / n
        sorted_nums = sorted(nums)
        median = sorted_nums[n // 2] if n % 2 else (sorted_nums[n // 2 - 1] + sorted_nums[n // 2]) / 2
        variance = sum((x - mean) ** 2 for x in nums) / n
        std_dev = variance ** 0.5

        result = (
            f"数据分析结果（共 {n} 个数据点）：\n"
            f"  均值: {mean:.2f}\n"
            f"  中位数: {median:.2f}\n"
            f"  最小值: {min(nums):.2f}\n"
            f"  最大值: {max(nums):.2f}\n"
            f"  标准差: {std_dev:.2f}\n"
            f"  总和: {sum(nums):.2f}"
        )
        return {"content": [{"type": "text", "text": result}]}


class ReportTool:
    """报告格式化工具 — 生成结构化报告"""

    def __init__(self):
        self.name = "format_report"
        self.description = "将散乱的信息格式化为结构化报告"
        self.inputSchema = {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "报告标题"},
                "content": {"type": "string", "description": "报告内容"}
            },
            "required": ["title", "content"]
        }

    def execute(self, title: str, content: str) -> dict:
        from datetime import datetime
        report = (
            f"{'='*50}\n"
            f"  报告：{title}\n"
            f"  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{'='*50}\n\n"
            f"{content}\n\n"
            f"{'='*50}\n"
            f"  报告结束"
        )
        return {"content": [{"type": "text", "text": report}]}


# ==================== 工具注册 ====================

_all_tools = [WebSearchTool(), CodeAnalysisTool(), DataAnalysisTool(), ReportTool()]

def get_agent_tools(tool_names: list = None) -> list:
    """按名称获取工具子集，方便给不同 Agent 分配不同工具"""
    if tool_names is None:
        return list(_all_tools)
    name_set = set(tool_names)
    return [t for t in _all_tools if t.name in name_set]


def find_tool(tools: list, name: str):
    """按名称查找工具"""
    for t in tools:
        if t.name == name:
            return t
    return None


def tools_to_openai_format(tools: list) -> list:
    """将工具列表转换为 OpenAI Function Calling 格式"""
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.inputSchema
            }
        }
        for t in tools
    ]
