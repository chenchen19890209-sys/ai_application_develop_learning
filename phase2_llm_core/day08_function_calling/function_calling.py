"""
function_calling.py
Function Calling 综合演示 — 使用原生openai SDK的tools参数

功能：
1. 基础Function Calling（天气查询）
2. 多工具场景（天气 + 计算器 + 时间）
3. 完整的Tool Calling Loop（循环直到完成）
4. 多工具并行调用
5. 工具调用的错误处理

学习目标：
1. 理解LLM如何选择和执行工具
2. 掌握tools参数的JSON Schema定义
3. 学会实现完整的Tool Calling Loop
4. 能构建多工具协作的场景
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from openai import OpenAI
import json  # 解析LLM返回的tool参数（JSON字符串）
import math  # 用于计算器工具
from datetime import datetime  # 用于时间工具

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


# ==================== 工具函数定义 ====================

def get_weather(city: str) -> dict:
    """获取指定城市的天气信息（模拟数据）"""
    # 模拟天气数据库
    weather_db = {
        "北京": {"temperature": 20, "condition": "晴", "humidity": 45},
        "上海": {"temperature": 25, "condition": "多云", "humidity": 60},
        "广州": {"temperature": 30, "condition": "小雨", "humidity": 75},
        "深圳": {"temperature": 28, "condition": "阴", "humidity": 70},
        "杭州": {"temperature": 22, "condition": "晴转多云", "humidity": 55},
    }
    if city in weather_db:
        return {"success": True, "city": city, "data": weather_db[city]}
    return {"success": False, "city": city, "message": f"未找到{city}的天气信息"}


def calculate(expression: str) -> dict:
    """安全的计算器 — 只支持基本数学运算"""
    try:
        # 白名单验证 — 只允许数字、运算符、空格、括号
        allowed = set("0123456789.+-*/()% eEpPiI")
        if not all(c in allowed for c in expression):
            return {"success": False, "message": "表达式包含不支持的字符"}
        # eval有安全风险，但配合白名单后可安全使用
        result = eval(expression, {"__builtins__": {}}, {"e": 2.718, "pi": 3.1416, "E": 2.718, "PI": 3.1416})
        return {"success": True, "expression": expression, "result": result}
    except Exception as e:
        return {"success": False, "expression": expression, "message": str(e)}


def get_current_time(timezone: str = "Asia/Shanghai") -> dict:
    """获取当前时间"""
    now = datetime.now()
    return {
        "success": True,
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()],
        "timezone": timezone
    }


# ==================== 工具Schema定义（JSON Schema格式）====================

# 新版API使用 tools 参数，每个工具用 {"type": "function", "function": {...}} 格式
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的当前天气信息，包括温度、天气状况和湿度。当用户询问天气时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如：北京、上海、广州、深圳、杭州"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "执行数学计算。支持加减乘除、幂运算、括号。当用户需要进行数学计算时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，例如：'2+3*4'、'(10+5)*2'、'3**4'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前日期和时间。当用户询问现在几点、今天日期时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "时区，默认为Asia/Shanghai"
                    }
                },
                "required": []
            }
        }
    }
]

# 工具执行映射 — 当LLM选择工具时，根据名称找到对应的Python函数
TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "calculate": calculate,
    "get_current_time": get_current_time,
}


# ==================== 第1部分：基础Function Calling ====================

def demo_basic_function_calling():
    """演示最基础的Function Calling流程"""
    print("=" * 60)
    print("📋 1. 基础Function Calling — 天气查询")
    print("-" * 60)

    # 步骤1: 发送用户问题 + 工具定义给LLM
    messages = [
        {"role": "system", "content": "你是生活助手，当需要实时信息时请使用工具。"},
        {"role": "user", "content": "北京今天天气怎么样？"}
    ]

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        tools=TOOLS,  # 告诉LLM有哪些可用工具
        tool_choice="auto"  # auto=LLM自动决定是否调用工具
    )

    # 步骤2: 检查LLM是否想调用工具
    choice = response.choices[0]
    if choice.message.tool_calls:
        # LLM决定调用工具！
        tool_call = choice.message.tool_calls[0]  # 取第一个工具调用
        func_name = tool_call.function.name  # 函数名
        func_args = json.loads(tool_call.function.arguments)  # 参数（JSON→dict）

        print(f"🔧 LLM选择调用: {func_name}")
        print(f"   参数: {func_args}")

        # 步骤3: 执行工具函数
        func = TOOL_FUNCTIONS[func_name]
        result = func(**func_args)  # **解包字典为关键字参数
        print(f"📊 执行结果: {result}")

        # 步骤4: 将结果返回给LLM，让它生成最终回复
        messages.append(choice.message)  # 添加LLM的工具调用请求
        messages.append({
            "role": "tool",  # tool角色=工具返回值
            "tool_call_id": tool_call.id,  # 绑定到具体的工具调用
            "content": json.dumps(result, ensure_ascii=False)
        })

        final_response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages
        )
        print(f"🤖 最终回复: {final_response.choices[0].message.content}")
    else:
        print(f"🤖 直接回复（未调用工具）: {choice.message.content}")


# ==================== 第2部分：多工具场景 ====================

def demo_multi_tools():
    """演示多工具协作场景"""
    print("\n" + "=" * 60)
    print("📋 2. 多工具协作场景")
    print("-" * 60)

    queries = [
        "上海天气怎么样？顺便帮我算一下 15*30+7 等于多少",
        "现在几点了？",
        "你好，请介绍一下自己",
    ]

    for query in queries:
        print(f"\n👤: {query}")
        print("-" * 30)

        messages = [
            {"role": "system", "content": "你是全能助手，可以查天气、做计算、看时间。"},
            {"role": "user", "content": query}
        ]

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        choice = response.choices[0]

        if choice.message.tool_calls:
            # 处理所有工具调用（可能并行调用多个）
            messages.append(choice.message)

            for tool_call in choice.message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                func = TOOL_FUNCTIONS[func_name]
                result = func(**func_args)
                print(f"  🔧 {func_name}({func_args}) → {result}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })

            # LLM整合所有工具结果
            final = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages
            )
            print(f"  🤖: {final.choices[0].message.content}")
        else:
            print(f"  🤖 (不用工具): {choice.message.content}")


# ==================== 第3部分：完整Tool Calling Loop ====================

def tool_loop(user_query: str, max_iterations: int = 5) -> str:
    """
    完整的Tool Calling Loop — Agent的核心！
    循环执行"LLM思考 → 工具调用 → 反馈结果"，直到LLM不再调用工具

    参数:
        user_query: 用户输入
        max_iterations: 最大循环次数（防止无限循环）

    返回:
        LLM的最终回复文本
    """
    messages = [
        {"role": "system", "content": "你是智能助手，可以使用工具解决用户的问题。"},
        {"role": "user", "content": user_query}
    ]

    for iteration in range(max_iterations):
        # 发送给LLM
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        choice = response.choices[0]

        # 如果没有工具调用 → LLM给出了最终回复
        if not choice.message.tool_calls:
            return choice.message.content

        # 有工具调用 → 执行并继续
        messages.append(choice.message)

        for tool_call in choice.message.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)
            func = TOOL_FUNCTIONS.get(func_name)

            if func:
                result = func(**func_args)
            else:
                result = {"success": False, "message": f"未知函数: {func_name}"}

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False)
            })

    return "已达到最大循环次数，但问题仍未完全解决"


def demo_tool_loop():
    """演示完整的Tool Calling Loop"""
    print("\n" + "=" * 60)
    print("📋 3. 完整Tool Calling Loop（Agent核心！）")
    print("-" * 60)

    test_cases = [
        "帮我查一下杭州的天气",
        "先查上海天气，然后算上海温度的平方",
        "现在几点了？帮我算一下当前小时数乘以60等于多少分钟",
    ]

    for query in test_cases:
        print(f"\n👤: {query}")
        print("-" * 30)
        answer = tool_loop(query)
        print(f"🤖: {answer}")


# ==================== 第4部分：从Python函数自动生成Tool Schema ====================

def demo_auto_schema():
    """演示如何从Python函数的类型提示自动生成JSON Schema"""
    print("\n" + "=" * 60)
    print("📋 4. 自动生成Tool Schema（最佳实践）")
    print("-" * 60)

    # 在Day04中我们学过Type Hints，现在它们发挥作用了！
    # 我们可以从Python函数签名自动生成工具的JSON Schema

    import inspect  # 用于读取函数签名

    def search_documents(query: str, limit: int = 5, category: str = "all") -> list[dict]:
        """搜索文档库，返回相关文章列表

        :param query: 搜索关键词
        :param limit: 返回结果数量，默认5
        :param category: 搜索范围，可选 'all', 'tech', 'news'
        """
        # 模拟搜索（实际项目中会调用真实搜索引擎）
        return [
            {"title": f"关于'{query}'的结果{i}", "score": 0.9 - i * 0.1}
            for i in range(min(limit, 3))
        ]

    # 从函数信息构建Schema（简化版Pydantic风格）
    sig = inspect.signature(search_documents)
    doc = inspect.getdoc(search_documents)

    properties = {}
    for name, param in sig.parameters.items():
        annotation = param.annotation if param.annotation != inspect.Parameter.empty else "string"
        type_map = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array"}
        json_type = type_map.get(annotation, "string")
        properties[name] = {
            "type": json_type,
            "description": f"参数: {name}"
        }

    schema = {
        "type": "function",
        "function": {
            "name": search_documents.__name__,
            "description": search_documents.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(properties.keys())[:1]  # 简化：第一个参数必填
            }
        }
    }

    print("从Python函数自动生成的Schema:")
    print(json.dumps(schema, indent=2, ensure_ascii=False))
    print("\n💡 这就是后续Agent框架中工具注册的底层原理！")
    print("   Day10将学习用MCP协议标准化这一过程")


def main():
    """主函数 — 按顺序运行所有演示"""
    print("=" * 60)
    print("Day 08: Function Calling（函数调用）")
    print("=" * 60)

    try:
        demo_basic_function_calling()
        demo_multi_tools()
        demo_tool_loop()
        demo_auto_schema()

        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        print("=" * 60)
        print("\n💡 今天的Tool Calling Loop就是Agent的核心引擎")
        print("   明天我们将在此基础上构建完整的Agent系统！")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()