"""
mcp_client.py — MCP Client + MCP Agent 完整实现

功能：
1. 通过 subprocess 启动 MCP Server 并建立 stdio 通信
2. 发送 initialize 握手请求，获取 Server 能力信息
3. 获取工具列表，转换为 OpenAI Function Calling 格式
4. MCPAgent：LLM 决策 + MCP 工具调用的完整 Agent

运行方式：
    python mcp_client.py

前置条件：
    - 已配置 .env 文件（OPENAI_API_KEY 等）
    - mcp_server.py 在同一目录下
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

import json
import subprocess  # 启动 MCP Server 子进程
import os
from typing import Optional

# 尝试导入 openai SDK
try:
    from openai import OpenAI
    HAS_OPENAI = bool(OPENAI_API_KEY)
except ImportError:
    HAS_OPENAI = False


# ==================== MCP Client 核心 ====================

class MCPClient:
    """MCP 客户端：管理与 MCP Server 的连接和通信"""

    def __init__(self, server_script: str = "mcp_server.py"):
        self.server_script = server_script
        self.process = None  # Server 子进程
        self.request_id = 0  # JSON-RPC 请求 ID 自增计数器
        self.tools = []  # 从 Server 获取的工具列表
        self.server_info = {}

    def start(self):
        """启动 MCP Server 子进程，建立 stdio 通信管道"""
        self.process = subprocess.Popen(
            [sys.executable, self.server_script],
            stdin=subprocess.PIPE,   # Client → Server
            stdout=subprocess.PIPE,  # Server → Client
            stderr=subprocess.PIPE,  # Server 日志
            text=True,               # 文本模式
            bufsize=1                # 行缓冲
        )

    def stop(self):
        """关闭 MCP Server 进程"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None

    def _next_id(self) -> int:
        """生成下一个 JSON-RPC 请求 ID"""
        self.request_id += 1
        return self.request_id

    def send_request(self, method: str, params: dict = None) -> dict:
        """发送 JSON-RPC 请求到 MCP Server，返回响应"""
        if self.process is None:
            raise RuntimeError("MCP Server 未启动，请先调用 start()")

        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {}
        }

        # 通过 stdin 发送请求
        request_json = json.dumps(request, ensure_ascii=False) + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()

        # 从 stdout 读取响应
        response_line = self.process.stdout.readline()
        if not response_line:
            raise ConnectionError("MCP Server 连接已断开")

        return json.loads(response_line)

    def initialize(self) -> dict:
        """MCP 握手：发送 initialize 请求"""
        response = self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "course-mcp-client", "version": "1.0.0"}
        })
        self.server_info = response.get("result", {}).get("serverInfo", {})
        return response

    def list_tools(self) -> list:
        """获取 Server 提供的所有工具定义"""
        response = self.send_request("tools/list")
        self.tools = response.get("result", {}).get("tools", [])
        return self.tools

    def call_tool(self, name: str, arguments: dict) -> dict:
        """调用指定的工具并获取执行结果"""
        response = self.send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
        return response.get("result", {})


# ==================== 工具格式转换 ====================

def mcp_tools_to_openai_format(mcp_tools: list) -> list:
    """将 MCP 工具定义转换为 OpenAI Function Calling 的 tools 格式"""
    openai_tools = []
    for tool in mcp_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["inputSchema"]  # MCP的inputSchema = OpenAI的parameters
            }
        })
    return openai_tools


# ==================== MCP Agent ====================

class MCPAgent:
    """基于 MCP 的 AI Agent：LLM 决策 + MCP 工具调用"""

    def __init__(self, client: MCPClient):
        self.client = client
        self.conversation_history = []  # 多轮对话历史
        if HAS_OPENAI:
            self.llm = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        else:
            self.llm = None

    def chat(self, user_message: str) -> str:
        """处理用户消息，LLM 决策后调用 MCP 工具"""
        system_prompt = (
            "你是一个智能助手，可以使用文件操作、时间查询、数学计算等工具。"
            "当用户提出请求时，判断是否需要调用工具。"
            "调用工具后，基于工具返回的结果生成自然语言回复。"
        )
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": user_message})

        # 获取 MCP 工具并转换格式
        tools = self.client.list_tools()
        openai_tools = mcp_tools_to_openai_format(tools)

        if self.llm is None:
            return self._simulate(user_message, tools)

        # LLM 决策
        response = self.llm.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=openai_tools,
            temperature=0.3
        )

        assistant_message = response.choices[0].message

        # 检查是否调用工具
        if assistant_message.tool_calls:
            tool_call = assistant_message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            print(f"  🔧 [Agent] 调用工具: {tool_name}({json.dumps(tool_args, ensure_ascii=False)})")

            # 通过 MCP 协议调用工具
            result = self.client.call_tool(tool_name, tool_args)
            tool_output = result.get("content", [{}])[0].get("text", "")

            print(f"  📤 [Agent] 工具返回: {tool_output[:100]}...")

            # 将工具结果反馈给 LLM
            messages.append({
                "role": "assistant",
                "tool_calls": [{
                    "id": tool_call.id, "type": "function",
                    "function": {"name": tool_name, "arguments": tool_call.function.arguments}
                }]
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_output
            })

            final_response = self.llm.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.7
            )
            reply = final_response.choices[0].message.content
        else:
            reply = assistant_message.content or "无法生成回复"

        # 保存对话历史
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": reply})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        return reply

    def _simulate(self, user_message: str, tools: list) -> str:
        """模拟模式：关键词匹配工具选择（无需真实 LLM）"""
        print("  ⚠️ [模拟模式] 未检测到 LLM API Key，使用关键词匹配")
        keyword_map = {
            "read_file": ["读", "查看", "打开", "看文件"],
            "list_directory": ["列目录", "列出", "目录", "ls"],
            "search_files": ["搜索", "查找", "包含", "grep"],
            "get_current_time": ["时间", "几点", "日期"],
            "calculate": ["计算", "算", "等于", "加", "减", "乘", "除"]
        }
        best_tool = None
        best_score = 0
        for tool_name, keywords in keyword_map.items():
            score = sum(1 for kw in keywords if kw in user_message.lower())
            if score > best_score:
                best_score = score
                best_tool = tool_name

        if best_tool and best_score > 0:
            print(f"  🔧 [模拟] 选择: {best_tool}")
            args = {
                "get_current_time": {"format": "datetime"},
                "calculate": {"expression": "100+200"},
                "list_directory": {"path": ".", "pattern": "*.py"},
                "read_file": {"path": "mcp_server.py"},
            }.get(best_tool, {"directory": ".", "query": "MCP"})
            result = self.client.call_tool(best_tool, args)
            return f"[模拟] {best_tool} 返回：\n{result.get('content', [{}])[0].get('text', '')}"
        return f"[模拟] 未匹配工具。可用: {', '.join(t['name'] for t in tools)}"


# ==================== 主流程 ====================

def main():
    """主流程：启动 Server → 握手 → 获取工具 → 交互对话"""
    print("=" * 60)
    print("  MCP Client — AI Agent 工具调用演示")
    print("=" * 60)

    # 确保 mcp_server.py 在同一目录
    server_path = Path(__file__).parent / "mcp_server.py"
    client = MCPClient(str(server_path))

    try:
        # 1. 启动 MCP Server
        print("\n🚀 启动 MCP Server...")
        client.start()

        # 2. 握手
        print("🤝 协议握手...")
        init_result = client.initialize()
        server_name = init_result.get("result", {}).get("serverInfo", {}).get("name", "unknown")
        print(f"✅ 已连接: {server_name}")

        # 3. 获取工具列表
        print("🔧 获取工具列表...")
        tools = client.list_tools()
        print(f"✅ 发现 {len(tools)} 个工具:")
        for tool in tools:
            print(f"  • {tool['name']}: {tool['description'][:60]}...")

        # 4. 创建 Agent 并演示
        agent = MCPAgent(client)
        print(f"\n{'=' * 60}")
        print("💬 MCP Agent 就绪！运行演示查询...")
        print(f"{'=' * 60}\n")

        demo_queries = [
            "现在几点了？",
            "帮我算一下 156 * 23 + 789",
            "列出当前目录下的 Python 文件",
            "在代码中搜索包含 'execute_tool' 的文件",
        ]

        for query in demo_queries:
            print(f"👤 用户: {query}")
            reply = agent.chat(query)
            print(f"🤖 Agent: {reply}\n")
            print("-" * 40)

        print("\n💡 演示完成！MCP 让工具定义与 Agent 解耦，任何 Agent 都能接入 MCP Server")

    except FileNotFoundError:
        print("❌ 找不到 mcp_server.py")
    except Exception as e:
        print(f"❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🛑 关闭 MCP Server...")
        client.stop()
        print("✅ 已关闭")


if __name__ == "__main__":
    main()