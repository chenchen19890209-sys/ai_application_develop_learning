"""
tools.py — 生产级 Agent 工具集

工具列表（MCP 兼容格式）：
1. SearchTool — 知识库搜索
2. CalculatorTool — 安全计算
3. WeatherTool — 天气查询

设计原则：纯 Python 类，MCP 标准格式，零外部依赖
"""


class SearchTool:
    """知识库搜索"""

    def __init__(self):
        self.name = "search"
        self.description = "搜索知识库获取信息"
        self.inputSchema = {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "搜索关键词"}},
            "required": ["query"]
        }
        self._kb = {
            "ai": "AI（人工智能）是模拟人类智能的计算机科学分支。2022 年 ChatGPT 发布后 AI 进入爆发期。主要应用：自然语言处理、计算机视觉、推荐系统。",
            "agent": "AI Agent 是自主感知、决策、执行的智能体。核心循环：感知→思考→行动→观察。ReAct 是最经典的 Agent 模式。",
            "mcp": "MCP（Model Context Protocol）是 AI 与工具之间的标准化通信协议，基于 JSON-RPC 2.0。实现了工具的跨框架、跨语言复用。",
            "rag": "RAG（检索增强生成）结合检索和生成技术。先检索相关文档，再交给 LLM 生成答案，有效减少幻觉。ChromaDB 是常用的向量数据库。",
            "production": "生产级 Agent 需要：配置管理、日志、缓存、重试、断路器、速率限制、输入验证、指标监控。这些关注点与业务逻辑解耦。",
        }

    def execute(self, query: str) -> dict:
        query_lower = query.lower()
        for keyword, content in self._kb.items():
            if keyword.lower() in query_lower:
                return {"content": [{"type": "text", "text": content}]}
        return {"content": [{"type": "text", "text": f"未找到与'{query}'相关的信息。可搜：AI、Agent、MCP、RAG、Production。"}]}


class CalculatorTool:
    """安全计算"""

    def __init__(self):
        self.name = "calculate"
        self.description = "执行安全的数学计算"
        self.inputSchema = {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "数学表达式"}},
            "required": ["expression"]
        }

    def execute(self, expression: str) -> dict:
        allowed = set("0123456789+-*/.()% eEpPiI")
        if not all(c in allowed for c in expression.replace(" ", "")):
            return {"content": [{"type": "text", "text": "表达式包含不允许的字符"}], "isError": True}
        try:
            result = eval(expression, {"__builtins__": {}}, {"e": 2.718, "pi": 3.1416})
            return {"content": [{"type": "text", "text": f"{expression} = {result}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"计算失败：{e}"}], "isError": True}


class WeatherTool:
    """天气查询"""

    def __init__(self):
        self.name = "get_weather"
        self.description = "查询城市天气"
        self.inputSchema = {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "城市名称"}},
            "required": ["city"]
        }
        self._weather = {
            "北京": "晴 22°C 湿度40%", "上海": "多云 26°C 湿度65%",
            "深圳": "阴 29°C 湿度72%", "广州": "雷阵雨 31°C 湿度80%",
        }

    def execute(self, city: str) -> dict:
        if city in self._weather:
            return {"content": [{"type": "text", "text": f"{city}天气：{self._weather[city]}"}]}
        return {"content": [{"type": "text", "text": f"未找到{city}的天气信息"}]}


# ==================== 工具注册 ====================

def get_production_tools() -> list:
    """获取生产 Agent 的工具列表"""
    return [SearchTool(), CalculatorTool(), WeatherTool()]


def find_tool(tools: list, name: str):
    for t in tools:
        if t.name == name:
            return t
    return None


def tools_to_openai_format(tools: list) -> list:
    return [
        {"type": "function", "function": {
            "name": t.name, "description": t.description, "parameters": t.inputSchema
        }}
        for t in tools
    ]
