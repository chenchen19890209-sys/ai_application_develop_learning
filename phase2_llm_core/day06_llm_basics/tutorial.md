# Day 06: LLM基础 — 与大语言模型交互

> 🎯 **学习目标**
>
> - 理解LLM的核心概念（Token、上下文窗口、Temperature）
> - 掌握使用原生 `openai` SDK 调用 LLM API
> - 理解原始HTTP请求与SDK的差异
> - 学会处理API错误和解析响应
> - 了解不同模型的选型策略

---

## 📖 前一天知识回顾

昨天我们完成了Python基础阶段：文件IO、异常处理、正则表达式、NumPy和Pandas。

**接下来进入AI核心领域！** 今天开始，我们将与大语言模型（LLM）直接交互。

---

## 📚 新知识讲解

### 1. 什么是LLM（大语言模型）？

**比喻**：LLM就像一个**博览群书的超级实习生**——读过互联网上几乎所有公开文本，能回答问题、写代码、翻译、创作，但需要你给出清晰的指令。

**定义**：LLM（Large Language Model）是一个基于Transformer架构、在海量文本上训练的神经网络，通过**预测下一个token**来逐字生成文本。

### 2. 核心概念：Token

**比喻**：Token就像文字的"积木块"——LLM不是按"字"来读文本，而是按"积木块"来拆解。

```
"我喜欢AI开发" → ["我", "喜欢", "AI", "开发"]  # 4个token（中文约1.5字/token）
"Hello World"   → ["Hello", " World"]          # 2个token（英文约0.75词/token）
```

**关键数字：**
- 1个 token ≈ 0.7 个汉字 ≈ 0.75 个英文单词
- DeepSeek V4 上下文窗口：约 128K tokens
- 定价按 token 计（输入便宜，输出贵）

### 3. 核心参数

| 参数 | 含义 | 建议值 |
|------|------|--------|
| **temperature** | 控制随机性（0-2） | 事实回答 0.1-0.3，创意 0.7-1.0 |
| **max_tokens** | 限制输出长度 | 1024（普通聊天），4096+（长文） |
| **top_p** | 核采样（替代temperature） | 0.9（与temperature二选一） |

### 4. 两种API调用方式

**方式一：原始HTTP请求**（理解底层协议）
```python
import requests
response = requests.post(
    f"{base_url}/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    json={"model": "deepseek-v4-flash", "messages": [...]}
)
result = response.json()
print(result["choices"][0]["message"]["content"])
```

**方式二：openai SDK**（生产推荐，更简洁）
```python
from openai import OpenAI
client = OpenAI(api_key=api_key, base_url=base_url)
response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "你好"}]
)
print(response.choices[0].message.content)
```

**本课程统一使用 openai SDK**——任何兼容 OpenAI 协议的 API（DeepSeek、NVIDIA NIM、通义千问等）都能用！

### 5. Chat Messages 结构

| role | 含义 | 示例 |
|------|------|------|
| `system` | 系统指令（设定AI角色） | "你是一个Python编程助手" |
| `user` | 用户消息 | "帮我写一个排序函数" |
| `assistant` | AI的回复 | 历史对话中AI说的内容 |

---

## 💡 实例演示

### 实例1：第一个 LLM API 调用

完整代码见 [first_llm_call.py](first_llm_call.py)，同时演示原始HTTP方式和openai SDK方式。

### 实例2：流式输出、参数调节

完整代码见 [first_llm_call.py](first_llm_call.py) 中的 `demo_streaming()` 和 `demo_parameters()`。

**运行方法：**
```bash
pip install openai python-dotenv
python first_llm_call.py
```

---

## ✍️ 练习题

### 练习1：基础题

1. 用openai SDK向LLM发送"请用一句话介绍Python"并打印回复
2. 用 `temperature=0.1` 和 `temperature=1.5` 分别生成，观察差异
3. 计算一段回复中有多少个token（1token≈0.7汉字估算即可）

### 练习2：进阶题

1. 实现一个简单的命令行聊天程序：用户输入→发送API→打印回复→继续对话
2. 尝试给system消息设置不同角色（"你是诗人" / "你是程序员"），观察回复风格差异
3. 处理异常：网络错误、API Key无效、超时

### 练习3：挑战题

实现一个多轮对话程序，要求：
- 保存完整对话历史（多轮上下文）
- 支持 /clear 清空对话
- 支持 /stats 显示token用量统计
- 支持 /temp 0.5 动态调整temperature

---

## 🔮 后一天知识展望

明天我们将学习 **Context Engineering（上下文工程）**——如何设计system prompt、管理对话上下文、构建工具描述，让LLM输出更高质量的结果。

---

## 📝 今日总结

今天我们学习了：
- ✅ LLM的核心概念：Token、Temperature、上下文窗口
- ✅ 用 openai SDK 调用 LLM API（生产推荐方式）
- ✅ Chat Messages 结构（system / user / assistant）
- ✅ 流式输出和参数调节

**关键要点：**
1. **Token 是LLM的基本单位**，中文约1.5字/token
2. **temperature 控制创造性**：低=稳定，高=随机
3. **openai SDK 兼容所有支持 OpenAI 协议的API**
4. **system消息设定角色**，是最重要的context

---

## 🚀 下一步

1. 完成所有练习题
2. 确认 `.env` 文件中有有效的 `OPENAI_API_KEY`
3. 尝试用不同的 temperature 值体验差异

**AI之旅正式开始！** 🚀

---

## 📖 参考资料

- [OpenAI Python SDK文档](https://github.com/openai/openai-python)
- [DeepSeek API文档](https://platform.deepseek.com/api-docs)
- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat)