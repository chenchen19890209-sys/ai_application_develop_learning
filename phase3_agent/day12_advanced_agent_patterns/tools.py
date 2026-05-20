"""
tools.py — 高级 Agent 模式共用的工具集

功能：
1. SearchTool — 知识库搜索工具（15+ 条目，覆盖 AI/科技/历史/地理）
2. CalculatorTool — 安全数学计算工具
3. get_tools_for_patterns() — 获取工具列表的便捷函数

设计原则：
- 零 LangChain 依赖 — 纯 Python 类实现
- MCP 兼容格式 — name/description/inputSchema + execute() 返回标准格式
- 工具可被 Plan-Execute、ReWOO、Self-Ask 三种模式共用
"""


class SearchTool:
    """知识库搜索工具 — 模拟多领域知识搜索"""

    def __init__(self):
        self.name = "search"  # 工具名称
        self.description = "在知识库中搜索信息，覆盖科技、历史、地理、科学等多个领域"  # 工具描述
        self.inputSchema = {  # MCP 标准参数定义
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词或问题"
                }
            },
            "required": ["query"]
        }
        # 知识库 — 覆盖多个领域，共 18 条
        self._kb = {
            "python": "Python 由 Guido van Rossum 于 1991 年创建。它是目前最流行的编程语言之一，广泛用于 AI、数据科学和 Web 开发。",
            "深度学习": "深度学习使用多层神经网络进行特征学习。2012 年 AlexNet 在 ImageNet 上的突破标志着深度学习时代的开始。",
            "transformer": "Transformer 架构由 Google 在 2017 年论文 'Attention Is All You Need' 中提出，它彻底改变了自然语言处理领域。",
            "agent": "AI Agent 是能够自主感知环境、做出决策并执行动作的智能体。ReAct、Plan-Execute、ReWOO 是主流 Agent 模式。",
            "rag": "RAG（检索增强生成）结合了信息检索和文本生成，先检索相关文档再交给 LLM 生成答案，有效减少幻觉。",
            "北京": "北京是中国的首都，位于华北平原北部，人口约 2189 万。著名景点包括故宫、长城、天坛等。",
            "上海": "上海是中国最大的城市和经济中心，位于长江入海口，人口约 2487 万。陆家嘴金融区是其标志性地标。",
            "爱因斯坦": "阿尔伯特·爱因斯坦（1879-1955）是德国出生的理论物理学家，提出了相对论。他因光电效应的解释获得 1921 年诺贝尔物理学奖。",
            "图灵": "艾伦·图灵（1912-1954）是英国数学家、计算机科学之父。他提出了图灵机概念和图灵测试，对 AI 领域有深远影响。",
            "苹果公司": "苹果公司由史蒂夫·乔布斯、史蒂夫·沃兹尼亚克和罗纳德·韦恩于 1976 年创立。现任 CEO 是蒂姆·库克（Tim Cook）。",
            "量子计算": "量子计算利用量子比特（qubit）的叠加和纠缠特性进行计算。它在密码学、药物发现和优化问题上有巨大潜力。",
            "气候变化": "全球气候变化主要由温室气体排放引起。巴黎协定（2015）旨在将全球变暖控制在 2°C 以内，力争 1.5°C。",
            "机器学习": "机器学习是 AI 的一个分支，让计算机从数据中学习模式而不需要显式编程。三大范式：监督学习、无监督学习、强化学习。",
            "神经网络": "人工神经网络受生物大脑启发，由相互连接的神经元层组成。反向传播算法是其训练的核心机制。",
            "mcp协议": "MCP（Model Context Protocol）是 Anthropic 提出的 AI 与外部工具通信的标准化协议。它基于 JSON-RPC 2.0，支持 stdio 和 HTTP+SSE 传输。",
            "gpu": "GPU（图形处理单元）最初用于图形渲染，现在已成为深度学习训练的核心硬件。NVIDIA 的 CUDA 平台主导了 AI 加速计算市场。",
            "token": "在 LLM 中，Token 是文本处理的最小单位。一个中文汉字约 1.5-2 个 token，英文单词约 1-2 个 token。Token 数量决定了模型的上下文窗口大小。",
            "prompt": "Prompt 是给 LLM 的输入指令。好的 Prompt 包含角色设定、任务描述、输出格式要求。Context Engineering 是对整套上下文的系统化设计。",
        }

    def execute(self, query: str) -> dict:
        """在知识库中搜索匹配的内容"""
        query_lower = query.lower()
        matches = []
        # 关键词匹配
        for keyword, content in self._kb.items():
            if keyword.lower() in query_lower or any(
                w in query_lower for w in keyword.lower().split()
            ):
                matches.append(f"【{keyword}】{content}")

        if not matches:
            return {"content": [{"type": "text", "text": f"未找到与 '{query}' 相关的信息。请尝试其他关键词。"}]}

        return {"content": [{"type": "text", "text": f"搜索结果（{len(matches)} 条）：\n\n" + "\n\n".join(matches)}]}


class CalculatorTool:
    """安全数学计算工具"""

    def __init__(self):
        self.name = "calculate"  # 工具名称
        self.description = "执行安全的数学表达式计算，支持加减乘除、幂运算、括号等"  # 工具描述
        self.inputSchema = {  # 参数定义
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，例如 '15 * 7 + 3' 或 '(100 - 20) / 4'"
                }
            },
            "required": ["expression"]
        }

    def execute(self, expression: str) -> dict:
        """安全计算数学表达式"""
        # 白名单字符集
        allowed = set("0123456789+-*/.()% eEpPiI")
        if not all(c in allowed for c in expression.replace(" ", "")):
            return {"content": [{"type": "text", "text": f"表达式包含不允许的字符"}], "isError": True}
        try:
            result = eval(expression, {"__builtins__": {}}, {
                "e": 2.718281828, "pi": 3.14159265,
                "E": 2.718281828, "PI": 3.14159265
            })
            return {"content": [{"type": "text", "text": f"{expression} = {result}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"计算失败：{str(e)}"}], "isError": True}


def get_tools_for_patterns() -> list:
    """获取用于高级 Agent 模式的工具实例列表"""
    return [SearchTool(), CalculatorTool()]


def find_tool_by_name(tools: list, name: str):
    """在工具列表中按名称查找工具"""
    for tool in tools:
        if tool.name == name:
            return tool
    return None


# ==================== 直接测试 ====================

if __name__ == "__main__":
    print("=" * 50)
    print("  Day 12 工具测试")
    print("=" * 50)

    tools = get_tools_for_patterns()
    for t in tools:
        print(f"\n🔧 {t.name}: {t.description[:60]}...")

    # 测试搜索
    print("\n--- 搜索测试 ---")
    r = tools[0].execute(query="量子计算")
    print(f"  {r['content'][0]['text'][:200]}...")

    # 测试计算
    print("\n--- 计算测试 ---")
    r = tools[1].execute(expression="25 * 4 + 10")
    print(f"  {r['content'][0]['text']}")
