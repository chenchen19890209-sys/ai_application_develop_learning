"""
tools.py — Agent 编排共用工具集

工具列表：
1. SearchTool — 知识库搜索
2. CalculatorTool — 数学计算
3. WeatherTool — 天气查询
4. TextTool — 文本分析（字数、关键词提取、情感判断）
"""
import re
from collections import Counter


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
            "python": "Python 语言，1991年由 Guido van Rossum 创建。最新版本 Python 3.12 于 2023 年发布。广泛应用于 AI/ML 领域。",
            "machine learning": "机器学习是 AI 分支，让计算机从数据中学习。使用算法如决策树、SVM、神经网络。scikit-learn 是流行框架。",
            "deep learning": "深度学习使用多层神经网络。PyTorch 和 TensorFlow 是两大主流框架。GPU 加速训练是关键。",
            "agent": "AI Agent 能够自主感知环境、决策并执行动作。ReAct、Plan-Execute、ReWOO 是经典模式。",
            "api": "API（应用程序接口）允许软件间通信。RESTful API 使用 HTTP 方法。OpenAI 的 API 格式已成为 LLM 调用的行业标准。",
            "database": "数据库用于存储和查询数据。SQL（关系型）和 NoSQL（非关系型）是两大类。常见的有 PostgreSQL、MongoDB、Redis。",
            "cloud": "云计算通过互联网提供计算资源。AWS、Azure、GCP 是三大云服务提供商。Serverless 架构简化了部署管理。",
            "docker": "Docker 是容器化平台，将应用及依赖打包为轻量级容器。Kubernetes 用于容器编排。",
            "security": "网络安全包括加密、认证、授权、审计。OWASP Top 10 列出了最关键的 Web 安全风险。SQL 注入和 XSS 是常见攻击。",
            "agile": "敏捷开发是一种迭代式软件开发方法。Scrum 是最流行的敏捷框架。强调快速迭代、持续反馈和团队协作。",
        }

    def execute(self, query: str) -> dict:
        query_lower = query.lower()
        matches = []
        for keyword, content in self._kb.items():
            if keyword.lower() in query_lower or any(w in query_lower for w in keyword.lower().split()):
                matches.append(f"【{keyword}】{content}")
        if not matches:
            return {"content": [{"type": "text", "text": f"未找到与'{query}'相关的信息"}]}
        return {"content": [{"type": "text", "text": "\n\n".join(matches)}]}


class CalculatorTool:
    """数学计算"""

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
        self.description = "查询城市天气信息"
        self.inputSchema = {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "城市名称"}},
            "required": ["city"]
        }
        self._weather = {
            "北京": "晴 22°C 湿度40%", "上海": "多云 26°C 湿度65%",
            "深圳": "阴 29°C 湿度72%", "杭州": "晴转多云 24°C 湿度55%",
        }

    def execute(self, city: str) -> dict:
        if city in self._weather:
            return {"content": [{"type": "text", "text": f"{city}天气：{self._weather[city]}"}]}
        return {"content": [{"type": "text", "text": f"未找到{city}的天气信息"}]}


class TextTool:
    """文本分析"""

    def __init__(self):
        self.name = "text_analysis"
        self.description = "分析文本：字数统计、关键词提取、情感倾向（简单）"
        self.inputSchema = {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "要分析的文本"},
                "analysis_type": {"type": "string", "enum": ["stats", "keywords", "sentiment", "all"],
                                  "description": "分析类型"}
            },
            "required": ["text"]
        }

    def execute(self, text: str, analysis_type: str = "all") -> dict:
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0
        lines = text.strip().split("\n")

        # 关键词提取 — 简单的词频统计
        words = re.findall(r"[\w一-鿿]+", text.lower())
        word_freq = Counter(w for w in words if len(w) > 1).most_common(10)

        # 简单情感判断
        positive_words = {"好", "优秀", "棒", "喜欢", "成功", "进步", "创新", "高效"}
        negative_words = {"差", "失败", "错误", "问题", "糟糕", "低效", "落后"}
        pos_count = sum(freq for word, freq in Counter(words).items() if word in positive_words)
        neg_count = sum(freq for word, freq in Counter(words).items() if word in negative_words)
        sentiment = "正面" if pos_count > neg_count else ("负面" if neg_count > pos_count else "中性")

        result_parts = [f"文本分析结果：\n  字符数: {char_count}\n  词数: {word_count}\n  行数: {len(lines)}"]

        if analysis_type in ("keywords", "all"):
            kw_text = "\n  ".join([f"{w}: {c}次" for w, c in word_freq[:10]])
            result_parts.append(f"  高频词:\n  {kw_text}")

        if analysis_type in ("sentiment", "all"):
            result_parts.append(f"  情感倾向: {sentiment}（正面词{pos_count}个，负面词{neg_count}个）")

        return {"content": [{"type": "text", "text": "\n".join(result_parts)}]}


# ==================== 工具注册 ====================

_all_tools = [SearchTool(), CalculatorTool(), WeatherTool(), TextTool()]


def get_orchestration_tools() -> list:
    """获取编排演示用的工具列表"""
    return list(_all_tools)


def find_tool(tools: list, name: str):
    for t in tools:
        if t.name == name:
            return t
    return None


def tools_to_openai_format(tools: list) -> list:
    return [
        {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.inputSchema}}
        for t in tools
    ]
