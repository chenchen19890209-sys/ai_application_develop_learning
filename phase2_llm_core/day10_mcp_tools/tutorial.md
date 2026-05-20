# Day 10: MCP协议 — 工具标准化的未来

> 🎯 **学习目标**
>
> - 理解MCP（Model Context Protocol）的架构：Host/Client/Server
> - 掌握MCP Server的实现：工具定义、JSON-RPC通信、stdio传输
> - 掌握MCP Client的实现：连接Server、获取工具列表、调用工具
> - 理解为什么MCP正在取代框架专有的工具注册方式
> - 实战：构建完整的MCP Server + Client + Agent系统

---

## 📖 前一天知识回顾

昨天我们实现了ReAct Agent：
- ✅ 在Agent类中手动注册工具（`register_tool()`）
- ✅ 工具定义和Agent耦合在一起

**问题：** 如果一个Agent想使用另一个项目开发的工具怎么办？如果把工具定义和Agent绑定，工具就没法跨项目复用。

**今天，MCP协议解决的就是这个问题！**

---

## 📚 新知识讲解

### 1. 什么是MCP（Model Context Protocol）？

**比喻**：MCP就像**USB-C接口**——在USB-C出现之前，每家手机公司都有自己专用的充电线（框架专有的Tool API）。MCP是一个统一的"接口标准"，任何Agent都能接入任何遵循MCP的工具服务。

```
┌─────────────────────────────────────────────────┐
│              MCP 架构 (Client-Server)             │
│                                                  │
│  ┌──────────────┐         ┌──────────────────┐  │
│  │  AI Agent    │───────▶│  MCP Server A    │  │
│  │  (Host)      │  调用   │  (天气预报工具)   │  │
│  │              │◀───────│                  │  │
│  └──────────────┘  结果   └──────────────────┘  │
│         │                                        │
│         │           ┌──────────────────┐        │
│         └──────────▶│  MCP Server B    │        │
│             调用    │  (文件操作工具)   │        │
│             ◀───────│                  │        │
│             结果    └──────────────────┘        │
│                                                  │
│  通信协议: JSON-RPC 2.0                         │
│  传输方式: stdio (本地) 或 HTTP+SSE (远程)      │
└─────────────────────────────────────────────────┘
```

### 2. MCP vs 框架专有的工具注册

| 维度 | 框架专有（LangChain @tool） | MCP 协议 |
|------|--------------------------|---------|
| 工具定义 | 框架特定的Python类 | 标准JSON Schema |
| 跨框架复用 | ❌ 绑定框架 | ✅ 任何Agent都能用 |
| 远程调用 | 需要额外封装 | ✅ HTTP+SSE原生支持 |
| 生态 | 框架的插件市场 | 所有语言都能实现Server |

### 3. MCP协议核心流程

```
1. Client启动Server子进程（或连接远程Server）
2. Client → Server: initialize（握手，交换能力信息）
3. Client → Server: tools/list（获取工具列表）
4. Client → Server: tools/call（调用工具）
5. Server → Client: 返回执行结果
6. 循环步骤4-5，直到任务完成
```

### 4. MCP Server 的工具定义

```python
TOOL_REGISTRY = {
    "get_weather": {
        "name": "get_weather",
        "description": "获取指定城市的天气信息",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称"
                }
            },
            "required": ["city"]
        }
    }
}
```

### 5. JSON-RPC 2.0 协议

MCP的底层通信使用JSON-RPC 2.0：
```json
// 请求
{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {...}}

// 响应
{"jsonrpc": "2.0", "id": 1, "result": {...}}
```

---

## 💡 实例演示

### 实例1：MCP Server — 5个工具的完整实现

完整代码见 [mcp_server.py](mcp_server.py) — 实现 read_file、list_directory、search_files、get_current_time、calculate 五个工具，基于stdio传输。

### 实例2：MCP Client — 连接Server、调用工具

完整代码见 [mcp_client.py](mcp_client.py) — 通过subprocess启动Server、建立JSON-RPC通信、获取工具列表并调用。

### 实例3：MCP Agent — LLM + MCP融合

`mcp_client.py` 中包含 `MCPAgent` 类，展示如何将MCP工具注入LLM的Tool Calling Loop。

**运行方法：**
```bash
# 先单独测试MCP Server
python mcp_server.py --demo

# 再运行完整的MCP Client + Agent
python mcp_client.py
```

---

## ✍️ 练习题

### 练习1：基础题

1. 给MCP Server新增一个工具（如 `get_joke` 获取笑话）
2. 运行 `python mcp_server.py --demo` 理解每个工具的功能
3. 修改 `mcp_client.py` 的 `demo_queries` 列表，测试不同的工具调用

### 练习2：进阶题

1. 将Day09的 `ReActAgent` 改造为MCP Agent（工具通过MCP协议获取，而非手动注册）
2. 实现多个MCP Server同时连接（天气Server + 文件Server），Agent自动选择
3. 给MCP Server添加工具调用的日志记录功能

### 练习3：挑战题

实现一个MCP工具市场（Tool Marketplace）：
- 一个注册中心，MCP Server可以向它注册
- Agent从注册中心发现可用的工具
- 支持工具的版本管理和热更新

---

## 🔮 后一天知识展望

**Phase 2（LLM核心能力）到此结束！** 明天我们进入Phase 3（Agent深度）的第一天：自定义工具与记忆系统，学习构建MCP-native的生产级工具和Agent的多层级记忆。

---

## 📝 今日总结

今天我们学习了：
- ✅ MCP协议的架构：Host/Client/Server三层模型
- ✅ JSON-RPC 2.0通信协议
- ✅ MCP Server的完整实现（5个工具、stdio传输）
- ✅ MCP Client的完整实现（启动Server、握手、工具调用）
- ✅ MCP Agent — LLM通过MCP使用工具

**关键要点：**
1. **MCP = 工具的USB-C接口**，统一了Agent和工具之间的通信标准
2. **MCP工具定义 = JSON Schema**，跨语言、跨框架可复用
3. **stdio适合本地**，HTTP+SSE适合远程
4. **MCP正在取代框架专有的工具注册方式**（LangChain @tool等）

---

## 🚀 下一步

1. 完成所有练习题
2. 理解MCP Server/Client的完整通信流程
3. 尝试把Day09的Agent改造为MCP Agent

**Phase 2完成！你已经掌握了LLM→Context→Function Calling→Agent→MCP的完整链路！** 🎉

---

## 📖 参考资料

- [MCP协议规范](https://spec.modelcontextprotocol.io/)
- [MCP官方文档](https://modelcontextprotocol.io/)
- [JSON-RPC 2.0规范](https://www.jsonrpc.org/specification)
- [Anthropic MCP介绍](https://www.anthropic.com/news/model-context-protocol)