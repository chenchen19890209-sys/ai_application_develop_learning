"""
mcp_server.py — MCP Server 完整实现

功能：
1. 提供文件操作工具（读文件、列目录、搜索文件）
2. 提供实用工具（获取当前时间、执行计算）
3. 基于 stdio 传输，使用 JSON-RPC 2.0 协议
4. 可作为独立进程运行，等待 MCP Client 连接

运行方式：
    python mcp_server.py           # stdio模式（被MCP Client调用）
    python mcp_server.py --demo    # 演示模式（直接测试工具）

MCP 协议版本：2024-11-05
"""
import sys
import io

# Windows 环境下强制 UTF-8 输出
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import json  # JSON-RPC 消息的序列化和反序列化
import os  # 文件系统操作
import re  # 正则搜索
import fnmatch  # Unix风格的文件名匹配
from datetime import datetime  # 获取当前时间


# ==================== 工具定义注册表 ====================
# 每个工具包含 name, description, inputSchema
# LLM 通过 description 来理解何时应该调用这个工具
TOOL_REGISTRY = {
    "read_file": {
        "name": "read_file",
        "description": "读取指定文件的内容。支持文本文件和代码文件。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "要读取的文件路径"
                },
                "encoding": {
                    "type": "string",
                    "default": "utf-8",
                    "description": "文件编码格式，默认 utf-8"
                }
            },
            "required": ["path"]
        }
    },
    "list_directory": {
        "name": "list_directory",
        "description": "列出指定目录下的所有文件和子目录",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "要列出的目录路径"
                },
                "pattern": {
                    "type": "string",
                    "description": "可选的文件名过滤模式，例如 *.py"
                }
            },
            "required": ["path"]
        }
    },
    "search_files": {
        "name": "search_files",
        "description": "在目录中递归搜索包含指定内容的文件。返回匹配的文件路径和行号。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "要搜索的根目录路径"
                },
                "query": {
                    "type": "string",
                    "description": "要搜索的文本内容（支持正则表达式）"
                },
                "file_pattern": {
                    "type": "string",
                    "default": "*",
                    "description": "要搜索的文件名模式，例如 *.py"
                }
            },
            "required": ["directory", "query"]
        }
    },
    "get_current_time": {
        "name": "get_current_time",
        "description": "获取当前的日期和时间",
        "inputSchema": {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "enum": ["datetime", "date", "time", "timestamp"],
                    "default": "datetime",
                    "description": "返回格式"
                }
            }
        }
    },
    "calculate": {
        "name": "calculate",
        "description": "执行安全的数学计算。支持加减乘除、幂运算、括号等。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，例如 '2 + 3 * 4'"
                }
            },
            "required": ["expression"]
        }
    }
}


def execute_tool(name: str, arguments: dict) -> dict:
    """根据工具名称和参数执行对应的操作，返回 MCP 标准格式的结果"""
    # ── 工具：读取文件 ──
    if name == "read_file":
        path = arguments.get("path", "")
        encoding = arguments.get("encoding", "utf-8")
        if not os.path.exists(path):
            return {"content": [{"type": "text", "text": f"错误：文件不存在 — {path}"}], "isError": True}
        try:
            with open(path, "r", encoding=encoding) as f:
                content = f.read()
            # 限制返回内容长度，避免超出 LLM 上下文窗口
            if len(content) > 50000:
                content = content[:50000] + f"\n\n... [文件过长，已截断，完整文件共 {len(content)} 字符]"
            return {"content": [{"type": "text", "text": content}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"读取文件失败：{str(e)}"}], "isError": True}

    # ── 工具：列出目录 ──
    elif name == "list_directory":
        path = arguments.get("path", ".")
        pattern = arguments.get("pattern", "*")
        if not os.path.isdir(path):
            return {"content": [{"type": "text", "text": f"错误：目录不存在 — {path}"}], "isError": True}
        try:
            items = []
            for item in sorted(os.listdir(path)):
                full_path = os.path.join(path, item)
                item_type = "DIR" if os.path.isdir(full_path) else "FILE"
                if pattern == "*" or fnmatch.fnmatch(item, pattern):
                    items.append(f"  [{item_type}] {item}")
            result = f"目录 {path} 的内容（共 {len(items)} 项）：\n" + "\n".join(items)
            return {"content": [{"type": "text", "text": result}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"列出目录失败：{str(e)}"}], "isError": True}

    # ── 工具：搜索文件内容 ──
    elif name == "search_files":
        directory = arguments.get("directory", ".")
        query = arguments.get("query", "")
        file_pattern = arguments.get("file_pattern", "*")
        if not os.path.isdir(directory):
            return {"content": [{"type": "text", "text": f"错误：目录不存在 — {directory}"}], "isError": True}
        try:
            matches = []
            for root, dirs, files in os.walk(directory):
                # 跳过隐藏目录和常见非源码目录
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in
                           ("node_modules", "__pycache__", "venv", ".git")]
                for filename in files:
                    if not fnmatch.fnmatch(filename, file_pattern):
                        continue
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            for line_no, line in enumerate(f, 1):
                                if re.search(query, line, re.IGNORECASE):
                                    matches.append(f"  {filepath}:{line_no}: {line.strip()[:120]}")
                    except Exception:
                        continue
            result = f"搜索 '{query}' 的结果（共 {len(matches)} 处匹配）：\n" + "\n".join(matches[:50])
            if len(matches) > 50:
                result += f"\n... 还有 {len(matches) - 50} 处匹配未显示"
            return {"content": [{"type": "text", "text": result}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"搜索失败：{str(e)}"}], "isError": True}

    # ── 工具：获取当前时间 ──
    elif name == "get_current_time":
        fmt = arguments.get("format", "datetime")
        now = datetime.now()
        time_map = {
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "timestamp": str(int(now.timestamp()))
        }
        result = time_map.get(fmt, time_map["datetime"])
        return {"content": [{"type": "text", "text": result}]}

    # ── 工具：数学计算 ──
    elif name == "calculate":
        expression = arguments.get("expression", "")
        try:
            allowed_chars = set("0123456789+-*/.() eEpPiI")
            if not all(c in allowed_chars for c in expression.replace(" ", "")):
                return {"content": [{"type": "text", "text": "错误：表达式中包含不允许的字符"}], "isError": True}
            result = eval(expression, {"__builtins__": {}}, {})
            return {"content": [{"type": "text", "text": f"计算结果：{expression} = {result}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"计算失败：{str(e)}"}], "isError": True}

    else:
        return {"content": [{"type": "text", "text": f"错误：未知工具 '{name}'"}], "isError": True}


# ==================== JSON-RPC 消息处理 ====================

def handle_request(request: dict) -> dict:
    """处理单个 JSON-RPC 请求，路由到对应的处理方法"""
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id")

    # initialize：协议握手
    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "course-mcp-server", "version": "1.0.0"},
                "capabilities": {"tools": {}}
            }
        }

    # tools/list：返回所有可用工具
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {"tools": list(TOOL_REGISTRY.values())}
        }

    # tools/call：执行工具
    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        result = execute_tool(tool_name, arguments)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    # notifications/initialized：无需响应
    elif method == "notifications/initialized":
        return None

    else:
        return {
            "jsonrpc": "2.0", "id": req_id,
            "error": {"code": -32601, "message": f"未知方法: {method}"}
        }


# ==================== stdio 传输层 ====================

def run_stdio_server():
    """通过标准输入输出运行 MCP Server"""
    print("[MCP Server] 启动中，等待客户端连接...", file=sys.stderr)
    print(f"[MCP Server] 已注册 {len(TOOL_REGISTRY)} 个工具", file=sys.stderr)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            if response is not None:
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0", "id": None,
                "error": {"code": -32700, "message": f"JSON 解析错误: {str(e)}"}
            }
            sys.stdout.write(json.dumps(error_response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


# ==================== 演示模式 ====================

def demo_mode():
    """演示模式：直接测试各个工具的功能"""
    print("=" * 60)
    print("MCP Server 演示模式 — 直接测试工具功能")
    print("=" * 60)

    tests = [
        ("get_current_time", {"format": "datetime"}, "获取当前时间"),
        ("calculate", {"expression": "15 * 7 + 3"}, "数学计算 15*7+3"),
        ("list_directory", {"path": ".", "pattern": "*.py"}, "列出Python文件"),
    ]

    for tool_name, args, desc in tests:
        print(f"\n📋 {desc}:")
        result = execute_tool(tool_name, args)
        text = result.get("content", [{}])[0].get("text", "无输出")
        print(f"  {text[:200]}")

    print(f"\n🔧 已注册的工具（共 {len(TOOL_REGISTRY)} 个）:")
    for tool_name, tool_def in TOOL_REGISTRY.items():
        print(f"  • {tool_name}: {tool_def['description']}")

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo_mode()
    else:
        run_stdio_server()