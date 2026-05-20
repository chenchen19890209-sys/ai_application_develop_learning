"""
context_engineering.py
Context Engineering（上下文工程）综合演示

功能：
1. System Message设计的A/B对比
2. 多维度上下文构建（角色 + 规则 + 格式 + 知识）
3. 上下文窗口管理（滑动窗口、token预算）
4. Few-shot示例的动态注入
5. 结构化输出控制

学习目标：
1. 理解Context Engineering的核心理念
2. 掌握System Message的设计方法
3. 学会管理上下文窗口大小
4. 能设计生产级的LLM上下文
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from openai import OpenAI
import time

# 初始化客户端
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


# ==================== 第1部分：System Message 设计 ====================

def demo_system_design():
    """演示System Message对输出质量的巨大影响"""
    print("=" * 60)
    print("📋 1. System Message 设计的 A/B 对比")
    print("-" * 60)

    question = "如何用Python读取CSV文件？"

    # A组：模糊的System Message（糟糕的设计）
    system_bad = "你是一个有用的助手"

    # B组：精心设计的System Message（好的设计）
    system_good = """你是一个Python编程专家，你的回答遵循以下规则：

## 角色
10年经验的Python高级工程师，擅长数据处理和系统开发

## 回答规则
1. 先给出1-2句话的简洁解释
2. 提供完整可运行的代码示例
3. 代码使用中文注释解释关键点
4. 指出常见陷阱和最佳实践

## 输出格式
```
[解释] 简短说明（1-2句）
[代码] 完整可运行的Python代码块
[注意] 需要留意的点
```

## 边界
你只回答编程相关问题，不确定的地方明确指出"""

    # A组测试
    response_a = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_bad},
            {"role": "user", "content": question}
        ],
        temperature=0.7, max_tokens=300, seed=42
    )
    print("\n❌ 糟糕的System Message（'你是一个有用的助手'）:")
    print(f"  回复长度: {len(response_a.choices[0].message.content)}字")
    print(f"  {response_a.choices[0].message.content[:200]}...")

    # B组测试
    response_b = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_good},
            {"role": "user", "content": question}
        ],
        temperature=0.7, max_tokens=300, seed=42
    )
    print(f"\n✅ 好的System Message（角色+规则+格式+边界）:")
    print(f"  回复长度: {len(response_b.choices[0].message.content)}字")
    print(f"  {response_b.choices[0].message.content}")

    print(f"\n💡 好的System Message让输出质量、结构、可用性全面提升")


# ==================== 第2部分：多维度上下文构建 ====================

def demo_multi_dimension_context():
    """演示如何构建多维度的上下文"""
    print("\n" + "=" * 60)
    print("📋 2. 多维度上下文构建")
    print("-" * 60)

    # 场景：构建一个能分析用户代码的AI Reviewer

    # 维度1: System Message（角色+规则）
    system_msg = """你是Code Reviewer，负责审查Python代码。

## 审查维度
1. 正确性：代码逻辑是否正确
2. 安全性：是否存在安全漏洞（SQL注入、XSS等）
3. 性能：是否有明显的性能问题
4. 风格：是否符合PEP 8规范
5. 可读性：命名是否清晰、注释是否充分

## 输出格式
```
[总体评价] 1句话总结
[问题列表]
  1. [严重程度: 高/中/低] 问题描述 → 建议修复方案
  2. ...
[亮点] 做得好的地方
```"""

    # 维度2: 注入领域知识（类似RAG的结果）
    domain_knowledge = """
## Python安全最佳实践
- 使用参数化查询防止SQL注入
- 使用bcrypt/scrypt存储密码，不用MD5
- subprocess.run()使用列表参数而非字符串拼接
- 文件路径使用pathlib而非字符串拼接
"""

    # 维度3: Few-shot示例
    few_shot_examples = """
### 审查示例
输入代码: ```python
query = "SELECT * FROM users WHERE name='" + name + "'"
```
审查结果:
[总体评价] 存在SQL注入漏洞，需要立即修复
[问题列表] 1. [高] SQL注入: 字符串拼接SQL → 使用参数化查询
"""

    # 维度4: 当前用户问题
    user_code = """
def login(username, password):
    query = f"SELECT * FROM users WHERE name='{username}' AND pass='{password}'"
    result = database.execute(query)
    return result
"""

    # 组装完整上下文
    user_msg = f"""{domain_knowledge}

{few_shot_examples}

请审查以下代码:

```python
{user_code}
```"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        temperature=0.3,  # 代码审查用低temperature
        max_tokens=500,
        seed=42
    )
    print(f"多维上下文审查结果:")
    print(response.choices[0].message.content)


# ==================== 第3部分：上下文窗口管理 ====================

def demo_context_budget():
    """演示上下文窗口的token预算管理"""
    print("\n" + "=" * 60)
    print("📋 3. 上下文窗口管理")
    print("-" * 60)

    # 模拟一个很长的对话历史
    long_history = [
        {"role": "system", "content": "你是一个Python助手"},
    ]
    # 模拟20轮对话
    for i in range(20):
        long_history.append({"role": "user", "content": f"第{i+1}个问题" * 10})
        long_history.append({"role": "assistant", "content": f"第{i+1}个回答" * 20})

    # 估算token数（简化版：中文约1.5字/token）
    def estimate_tokens(messages):
        """估算消息列表的总token数"""
        total_chars = sum(len(m["content"]) for m in messages)
        return int(total_chars / 1.5)  # 中文约1.5字/token

    total_tokens = estimate_tokens(long_history)
    print(f"完整对话: {len(long_history)}条消息, 约{total_tokens} tokens")

    # 策略1: 滑动窗口 — 保留最近N轮
    def sliding_window(messages, max_turns=5):
        """保留system消息 + 最近N轮对话"""
        system = [m for m in messages if m["role"] == "system"]
        dialog = [m for m in messages if m["role"] != "system"]
        # 每轮包含user+assistant，所以保留max_turns*2条消息
        return system + dialog[-(max_turns * 2):]

    windowed = sliding_window(long_history, max_turns=5)
    window_tokens = estimate_tokens(windowed)
    print(f"滑动窗口(5轮): {len(windowed)}条消息, 约{window_tokens} tokens")
    print(f"  压缩比: {window_tokens/total_tokens*100:.1f}%")

    # 策略2: System固定 + 最近3轮 + 当前问题
    def budget_aware_window(messages, max_tokens=4000):
        """根据token预算裁剪上下文"""
        system = [m for m in messages if m["role"] == "system"]
        budget_for_system = estimate_tokens(system)
        remaining = max_tokens - budget_for_system - 200  # 200留给回复

        dialog = [m for m in messages if m["role"] != "system"]
        kept = []
        kept_tokens = 0
        # 从最新往前取，直到接近预算
        for msg in reversed(dialog):
            msg_tokens = int(len(msg["content"]) / 1.5)
            if kept_tokens + msg_tokens > remaining:
                break
            kept.insert(0, msg)  # 保持时间顺序
            kept_tokens += msg_tokens

        return system + kept

    budgeted = budget_aware_window(long_history, max_tokens=2000)
    budget_tokens = estimate_tokens(budgeted)
    print(f"预算管理(2000 tokens): {len(budgeted)}条消息, 约{budget_tokens} tokens")
    print(f"  压缩比: {budget_tokens/total_tokens*100:.1f}%")


# ==================== 第4部分：结构化输出控制 ====================

def demo_structured_output():
    """演示如何通过上下文设计控制输出格式"""
    print("\n" + "=" * 60)
    print("📋 4. 结构化输出控制")
    print("-" * 60)

    # 场景：让LLM以结构化格式输出图书信息
    system = """你是图书信息提取助手。当用户提供书名时，你需要返回该书的JSON格式信息。

## 输出格式（严格遵守）
返回一个JSON对象，包含以下字段：
```json
{
  "title": "书名",
  "author": "作者",
  "year": 出版年份(数字),
  "tags": ["标签1", "标签2"],
  "summary": "一句话简介(不超过50字)",
  "confidence": 置信度(0.0-1.0)
}
```

## 规则
- 仅输出JSON，不要任何额外文字
- 不确定的信息用null
- confidence低于0.5时设置tags为空数组
"""

    books = ["三体", "哈利波特与魔法石", "深度学习"]

    for book in books:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": book}
            ],
            temperature=0.3,  # 结构化输出用低temperature
            max_tokens=300,
            seed=42
        )
        import json
        content = response.choices[0].message.content
        # 尝试去除可能的markdown代码块标记
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]  # 去掉```json
            if content.endswith("```"):
                content = content[:-3]
        try:
            parsed = json.loads(content)
            print(f"\n《{book}》:")
            print(f"  作者: {parsed.get('author', '?')}")
            print(f"  年份: {parsed.get('year', '?')}")
            print(f"  标签: {parsed.get('tags', [])}")
            print(f"  置信度: {parsed.get('confidence', 0)}")
        except json.JSONDecodeError:
            print(f"\n《{book}》: JSON解析失败")
            print(f"  原始输出: {content[:200]}")


def main():
    """主函数 — 按顺序运行所有演示"""
    print("=" * 60)
    print("Day 07: Context Engineering（上下文工程）")
    print("=" * 60)

    try:
        demo_system_design()
        demo_multi_dimension_context()
        demo_context_budget()
        demo_structured_output()

        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        print("=" * 60)
        print("\n💡 核心要点:")
        print("  1. System Message = 给AI的岗位说明书")
        print("  2. Context = LLM看到的全部信息（system + tools + knowledge + history + user）")
        print("  3. 好的上下文设计比反复调prompt更有效")
        print("  4. 上下文窗口有上限，需要管理token预算")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()