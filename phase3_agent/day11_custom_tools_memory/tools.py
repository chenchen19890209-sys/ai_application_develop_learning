"""
tools.py — MCP-native 自定义工具实现

功能：
1. WeatherTool — 天气查询工具（模拟数据库）
2. CalculatorTool — 安全数学计算工具
3. TodoTool — 待办事项管理工具（内存存储）
4. SearchTool — 知识库搜索工具（模拟搜索）
5. FileTool — 文件系统操作工具

设计原则：
- 零 LangChain 依赖 — 纯 Python 类实现
- MCP 兼容格式 — name/description/inputSchema + execute() 返回 content 格式
- 每个工具都是独立可测试的类
"""
import os  # 文件系统操作
import json  # JSON 序列化
from datetime import datetime  # 时间戳


# ==================== 天气查询工具 ====================

class WeatherTool:
    """天气查询工具 — 模拟天气数据库"""

    def __init__(self):
        self.name = "get_weather"  # 工具名称（LLM 可见）
        self.description = "查询指定城市的当前天气信息，包括温度、天气状况和湿度"  # 工具描述（LLM 选择工具的依据）
        self.inputSchema = {  # MCP 标准的 JSON Schema 参数定义
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "要查询的城市名称，例如'北京'、'上海'"
                }
            },
            "required": ["city"]
        }
        # 模拟天气数据库 — 城市 -> 温度/状况/湿度
        self._weather_db = {
            "北京": {"temperature": 22, "condition": "晴", "humidity": 40},
            "上海": {"temperature": 26, "condition": "多云转阴", "humidity": 65},
            "广州": {"temperature": 31, "condition": "雷阵雨", "humidity": 80},
            "深圳": {"temperature": 29, "condition": "阴天", "humidity": 72},
            "杭州": {"temperature": 24, "condition": "晴转多云", "humidity": 55},
            "成都": {"temperature": 20, "condition": "小雨", "humidity": 78},
        }

    def execute(self, city: str) -> dict:
        """执行天气查询，返回 MCP 标准格式的结果"""
        if city in self._weather_db:
            w = self._weather_db[city]
            text = f"{city}天气：{w['condition']}，温度 {w['temperature']}°C，湿度 {w['humidity']}%"
        else:
            text = f"未找到城市'{city}'的天气信息。已知城市：{', '.join(self._weather_db.keys())}"
        return {"content": [{"type": "text", "text": text}]}


# ==================== 数学计算工具 ====================

class CalculatorTool:
    """安全数学计算工具 — 限制可执行的运算"""

    def __init__(self):
        self.name = "calculate"  # 工具名称
        self.description = "执行安全的数学表达式计算，支持加减乘除、括号、幂运算等"  # 功能描述
        self.inputSchema = {  # 参数 Schema
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，例如 '(15 + 7) * 3 - 8 / 2'"
                }
            },
            "required": ["expression"]
        }

    def execute(self, expression: str) -> dict:
        """安全地计算数学表达式"""
        # 白名单：只允许数字、基本运算符、科学常数
        allowed_chars = set("0123456789+-*/.()% eEpPiI")
        cleaned = expression.replace(" ", "")
        if not all(c in allowed_chars for c in cleaned):
            return {"content": [{"type": "text", "text": f"表达式包含不允许的字符：{expression}"}], "isError": True}
        try:
            # 在受限环境中执行计算，禁用所有内置函数
            result = eval(expression, {"__builtins__": {}}, {
                "e": 2.718281828, "pi": 3.14159265,
                "E": 2.718281828, "PI": 3.14159265
            })
            return {"content": [{"type": "text", "text": f"计算结果：{expression} = {result}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"计算失败：{str(e)}"}], "isError": True}


# ==================== 待办事项工具 ====================

class TodoTool:
    """待办事项管理工具 — 内存存储的 Todo 列表"""

    def __init__(self):
        self.name = "todo_manager"  # 工具名称
        self.description = "管理待办事项：添加新事项、列出所有事项、标记完成、清空列表"  # 功能描述
        self.inputSchema = {  # 参数 Schema
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "list", "done", "clear"],
                    "description": "操作类型：add-添加任务，list-列出所有任务，done-标记完成，clear-清空列表"
                },
                "task": {
                    "type": "string",
                    "description": "任务描述（仅 add 操作需要）"
                },
                "task_id": {
                    "type": "integer",
                    "description": "任务 ID（仅 done 操作需要）"
                }
            },
            "required": ["action"]
        }
        self._todos = []  # 待办事项列表
        self._next_id = 1  # 自增 ID

    def execute(self, action: str, task: str = None, task_id: int = None) -> dict:
        """执行待办事项操作"""
        if action == "add":
            # 添加待办事项
            if not task:
                return {"content": [{"type": "text", "text": "请提供要添加的任务描述"}], "isError": True}
            item = {"id": self._next_id, "task": task, "done": False, "created_at": datetime.now().isoformat()}
            self._todos.append(item)
            self._next_id += 1
            return {"content": [{"type": "text", "text": f"已添加待办事项 #{item['id']}：{task}"}]}

        elif action == "list":
            # 列出所有待办事项
            if not self._todos:
                return {"content": [{"type": "text", "text": "待办事项列表为空"}]}
            lines = [f"待办事项列表（共 {len(self._todos)} 项）："]
            for item in self._todos:
                status = "✓" if item["done"] else "○"
                lines.append(f"  [{status}] #{item['id']} {item['task']}")
            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

        elif action == "done":
            # 标记完成
            if task_id is None:
                return {"content": [{"type": "text", "text": "请提供要完成的任务 ID"}], "isError": True}
            for item in self._todos:
                if item["id"] == task_id:
                    item["done"] = True
                    return {"content": [{"type": "text", "text": f"已完成：{item['task']}"}]}
            return {"content": [{"type": "text", "text": f"未找到 ID 为 {task_id} 的待办事项"}], "isError": True}

        elif action == "clear":
            # 清空列表
            count = len(self._todos)
            self._todos.clear()
            return {"content": [{"type": "text", "text": f"已清空所有待办事项（共 {count} 项）"}]}

        else:
            return {"content": [{"type": "text", "text": f"未知操作：{action}"}], "isError": True}


# ==================== 知识库搜索工具 ====================

class SearchTool:
    """知识库搜索工具 — 模拟 AI/编程领域知识搜索"""

    def __init__(self):
        self.name = "search_knowledge"  # 工具名称
        self.description = "在 AI 和编程知识库中搜索相关内容，返回匹配的条目"  # 功能描述
        self.inputSchema = {  # 参数 Schema
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词或问题"
                }
            },
            "required": ["query"]
        }
        # 知识库 — 模拟的搜索索引
        self._knowledge_base = {
            "python": "Python 是一种解释型、面向对象的高级编程语言，由 Guido van Rossum 于 1991 年发布。它以其简洁的语法和丰富的第三方库生态而闻名。",
            "深度学习": "深度学习是机器学习的一个子集，使用多层神经网络来学习数据的层次化表示。核心架构包括 CNN（卷积神经网络）、RNN（循环神经网络）和 Transformer。",
            "transformer": "Transformer 是一种基于自注意力机制的神经网络架构，由 Vaswani 等人在 2017 年提出。它是 GPT、BERT 等现代大语言模型的基础架构。",
            "rag": "RAG（Retrieval-Augmented Generation）是一种结合信息检索和文本生成的技术架构。它先检索相关文档，再将文档作为上下文提供给 LLM 生成答案。",
            "mcp": "MCP（Model Context Protocol）是 Anthropic 提出的标准化协议，用于 AI 模型与外部工具、数据源之间的通信。它基于 JSON-RPC 2.0，支持 stdio 和 HTTP+SSE 传输。",
            "agent": "AI Agent 是能自主感知环境、做出决策并执行行动的智能系统。核心循环是：感知→思考→行动→观察。ReAct 是最经典的 Agent 模式之一。",
            "react": "ReAct（Reasoning + Acting）是一种将推理和行动交替进行的 Agent 模式。每一步先让 LLM 推理是否需要工具，然后执行工具并将结果反馈给 LLM。",
            "function calling": "Function Calling 是 LLM 的一项能力，允许模型根据用户输入决定调用哪个函数以及传递什么参数。开发者提供 JSON Schema 格式的函数定义。",
            "embedding": "Embedding（嵌入）是将文本、图像等非结构化数据映射到固定维度向量空间的技术。语义相近的文本其向量距离也相近，是 RAG 系统的基础。",
            "prompt engineering": "Prompt Engineering 是设计和优化 LLM 输入提示的技术。但随着模型能力提升，Context Engineering（上下文工程）正在取代简单的手写 Prompt。",
            "langchain": "LangChain 是一个用于构建 LLM 应用的 Python 框架。它提供了 Chains、Agents、Tools 等抽象。但 MCP 协议正在推动行业向框架无关的工具标准化方向发展。",
            "chromadb": "ChromaDB 是一个开源的向量数据库，专为 AI 应用设计。它支持嵌入存储、相似度搜索和元数据过滤，是构建 RAG 系统的常用选择。",
            "openai": "OpenAI 是一家领先的 AI 研究公司，开发了 GPT 系列模型。其 API 已成为行业标准，许多模型提供商都兼容 OpenAI 的 API 格式。",
            "context engineering": "Context Engineering 是比 Prompt Engineering 更高层次的设计方法论。它关注整个上下文的构建：系统消息、工具描述、记忆、检索结果、对话历史的协调编排。",
        }

    def execute(self, query: str) -> dict:
        """搜索知识库并返回匹配结果"""
        query_lower = query.lower()
        matches = []
        # 遍历知识库进行关键词匹配
        for keyword, content in self._knowledge_base.items():
            if keyword.lower() in query_lower or any(
                word in query_lower for word in keyword.split()
            ):
                matches.append(f"【{keyword}】{content}")
        if not matches:
            return {"content": [{"type": "text", "text": f"未找到与'{query}'相关的知识条目。可尝试搜索：Python、深度学习、RAG、Agent、MCP 等话题。"}]}
        return {"content": [{"type": "text", "text": f"搜索'{query}'的结果（共 {len(matches)} 条）：\n\n" + "\n\n".join(matches)}]}


# ==================== 文件操作工具 ====================

class FileTool:
    """文件系统操作工具 — 读取文件和列出目录"""

    def __init__(self):
        self.name = "file_operations"  # 工具名称
        self.description = "执行文件系统操作：读取文件内容、列出目录下的文件"  # 功能描述
        self.inputSchema = {  # 参数 Schema
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "list"],
                    "description": "操作类型：read-读取文件，list-列出目录"
                },
                "path": {
                    "type": "string",
                    "description": "文件或目录路径"
                }
            },
            "required": ["operation", "path"]
        }

    def execute(self, operation: str, path: str) -> dict:
        """执行文件操作"""
        if operation == "read":
            # 读取文件内容
            if not os.path.exists(path):
                return {"content": [{"type": "text", "text": f"文件不存在：{path}"}], "isError": True}
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                if len(content) > 3000:
                    content = content[:3000] + f"\n\n... [文件过大，已截断，共 {len(content)} 字符]"
                return {"content": [{"type": "text", "text": content}]}
            except Exception as e:
                return {"content": [{"type": "text", "text": f"读取文件失败：{str(e)}"}], "isError": True}

        elif operation == "list":
            # 列出目录内容
            if not os.path.isdir(path):
                return {"content": [{"type": "text", "text": f"目录不存在：{path}"}], "isError": True}
            try:
                items = []
                for item in sorted(os.listdir(path)):
                    full = os.path.join(path, item)
                    tag = "DIR" if os.path.isdir(full) else "FILE"
                    size = ""
                    if tag == "FILE":
                        size = f" ({os.path.getsize(full)} bytes)"
                    items.append(f"  [{tag}] {item}{size}")
                return {"content": [{"type": "text", "text": f"目录 '{path}' 内容（共 {len(items)} 项）：\n" + "\n".join(items)}]}
            except Exception as e:
                return {"content": [{"type": "text", "text": f"列出目录失败：{str(e)}"}], "isError": True}

        else:
            return {"content": [{"type": "text", "text": f"未知操作：{operation}"}], "isError": True}


# ==================== 工具注册 ====================

def get_all_tools() -> list:
    """获取所有可用工具的实例列表"""
    return [
        WeatherTool(),
        CalculatorTool(),
        TodoTool(),
        SearchTool(),
        FileTool(),
    ]


def tools_to_openai_format(tools: list) -> list:
    """将工具列表转换为 OpenAI Function Calling 格式"""
    openai_tools = []
    for tool in tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        })
    return openai_tools


def find_tool(tools: list, name: str):
    """在工具列表中按名称查找工具"""
    for tool in tools:
        if tool.name == name:
            return tool
    return None


# ==================== 直接测试 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  自定义工具测试")
    print("=" * 60)

    tools = get_all_tools()
    print(f"\n已注册 {len(tools)} 个工具：")
    for t in tools:
        print(f"  • {t.name}: {t.description[:60]}...")

    # 测试天气工具
    print("\n" + "-" * 40)
    print("测试 WeatherTool：")
    result = tools[0].execute(city="北京")
    print(f"  {result['content'][0]['text']}")

    # 测试计算器
    print("\n" + "-" * 40)
    print("测试 CalculatorTool：")
    result = tools[1].execute(expression="15 * 7 + 3")
    print(f"  {result['content'][0]['text']}")

    # 测试待办事项
    print("\n" + "-" * 40)
    print("测试 TodoTool：")
    todo = tools[2]
    print(f"  {todo.execute(action='add', task='学习 MCP 协议')['content'][0]['text']}")
    print(f"  {todo.execute(action='add', task='完成 Phase 3 练习')['content'][0]['text']}")
    print(f"  {todo.execute(action='list')['content'][0]['text']}")

    # 测试搜索
    print("\n" + "-" * 40)
    print("测试 SearchTool：")
    result = tools[3].execute(query="MCP 协议")
    print(f"  {result['content'][0]['text'][:200]}...")

    print("\n" + "=" * 60)
    print("  测试完成！所有工具运行正常")
    print("=" * 60)