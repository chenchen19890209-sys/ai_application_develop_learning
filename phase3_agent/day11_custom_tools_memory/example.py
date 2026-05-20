"""
example.py — Day 11 完整演示：自定义工具 + 记忆系统

演示内容：
1. 自定义工具展示 — 逐个测试 5 个工具
2. 多轮对话记忆 — ShortTermMemory 在对话中的表现
3. 长期记忆 — Agent 记住用户偏好并跨查询使用
4. 复杂任务 — 需要多工具 + 多记忆协同的任务
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools import get_all_tools, find_tool
from memory import WorkingMemory, ShortTermMemory, LongTermMemory
from agent_with_memory import MemoryAgent
import json


def demo_tools_showcase():
    """演示 1：自定义工具逐个测试"""
    print("\n" + "=" * 60)
    print("  📋 演示 1：自定义工具展示")
    print("=" * 60)

    tools = get_all_tools()
    print(f"\n已加载 {len(tools)} 个工具：")
    for t in tools:
        print(f"  🔧 {t.name}: {t.description[:70]}...")

    # 测试天气工具
    print("\n--- WeatherTool ---")
    weather = find_tool(tools, "get_weather")
    r = weather.execute(city="深圳")
    print(f"  {r['content'][0]['text']}")

    # 测试计算器
    print("\n--- CalculatorTool ---")
    calc = find_tool(tools, "calculate")
    r = calc.execute(expression="(100 + 50) * 3 - 25 / 5")
    print(f"  {r['content'][0]['text']}")

    # 测试知识搜索
    print("\n--- SearchTool ---")
    search = find_tool(tools, "search_knowledge")
    r = search.execute(query="Agent RAG")
    print(f"  {r['content'][0]['text'][:300]}...")

    # 测试待办事项
    print("\n--- TodoTool ---")
    todo = find_tool(tools, "todo_manager")
    print(f"  {todo.execute(action='add', task='学习 Day 11 内容')['content'][0]['text']}")
    print(f"  {todo.execute(action='add', task='完成练习题')['content'][0]['text']}")
    print(f"  {todo.execute(action='done', task_id=1)['content'][0]['text']}")
    print(f"  {todo.execute(action='list')['content'][0]['text']}")

    # 测试文件工具
    print("\n--- FileTool ---")
    ft = find_tool(tools, "file_operations")
    current_dir = str(Path(__file__).parent)
    r = ft.execute(operation="list", path=current_dir)
    print(f"  {r['content'][0]['text'][:300]}...")


def demo_short_term_memory():
    """演示 2：短期记忆 — 多轮对话"""
    print("\n" + "=" * 60)
    print("  📋 演示 2：短期记忆 — 多轮对话")
    print("=" * 60)

    sm = ShortTermMemory(max_turns=5)

    # 模拟多轮对话
    conversations = [
        ("你好！我叫小明。", "你好小明！很高兴认识你。有什么我可以帮你的吗？"),
        ("我喜欢编程，特别是 Python。", "Python 是很棒的语言！我也很喜欢用它来构建 AI 应用。"),
        ("我刚才说我叫什么名字？", "你说你叫小明。我也记得你喜欢 Python 编程。"),
    ]

    for user_msg, assistant_msg in conversations:
        sm.add_user_message(user_msg)
        sm.add_assistant_message(assistant_msg)
        print(f"\n  👤 用户: {user_msg}")
        print(f"  🤖 助手: {assistant_msg}")

    print(f"\n  📊 当前对话历史共 {len(sm)} 条消息")
    print(f"\n  {sm.to_context_string()}")


def demo_long_term_memory():
    """演示 3：长期记忆 — 跨会话信息保持"""
    print("\n" + "=" * 60)
    print("  📋 演示 3：长期记忆 — 用户偏好持久化")
    print("=" * 60)

    lm = LongTermMemory()
    lm.clear_all()  # 清空之前的记忆

    # 模拟：用户在多轮对话中透露了自己的信息
    print("\n  -- 第一轮对话 --")
    print("  👤 用户: 我叫张伟，住在上海，是一名数据分析师。")
    print("  👤 用户: 我比较关注深度学习和 RAG 技术的进展。")

    # LLM 从对话中提取关键信息
    conversation1 = "用户: 我叫张伟，住在上海，是一名数据分析师。\n用户: 我比较关注深度学习和 RAG 技术的进展。"
    extracted = lm.summarize_and_store(conversation1)
    print(f"  📝 提取到的长期记忆: {extracted}")

    # 模拟：第二轮对话（新会话）
    print("\n  -- 第二轮对话（新会话）--")
    print(f"  📖 从长期记忆加载：")
    print(f"  {lm.get_all_memories()}")

    # 模拟：Agent 利用长期记忆个性化回复
    user_city = lm.recall("user_city") or "未知城市"
    user_interest = lm.recall("user_interest") or "通用话题"
    print(f"\n  💡 Agent 可以利用这些记忆来个性化回复：")
    print(f"     '张伟你好！我知道你在{user_city}，"
          f"作为数据分析师，你应该会对最新的{user_interest}进展感兴趣...'")


def demo_memory_agent():
    """演示 4：MemoryAgent 完整流程"""
    print("\n" + "=" * 60)
    print("  📋 演示 4：MemoryAgent — 完整 Agent 流程")
    print("=" * 60)

    agent = MemoryAgent()

    # 预处理：设置用户偏好到长期记忆
    agent.long_term.remember("user_name", "小李")
    agent.long_term.remember("user_preference", "喜欢简洁的技术解释")

    print("\n  💬 开始对话...")
    print("  (Agent 会利用长期记忆中的用户信息)\n")

    # 查询 1：简单天气查询（单工具调用）
    query1 = "北京今天天气怎么样？"
    print(f"  👤 用户: {query1}")
    try:
        reply1 = agent.run(query1)
        print(f"\n  🤖 Agent: {reply1}")
    except Exception as e:
        print(f"  ⚠️ LLM 调用失败（可能 API Key 未配置）: {e}")
        print(f"  💡 工具和记忆系统本身已就绪，需要 API Key 来驱动 LLM 决策")

    print(f"\n  {agent.get_memory_report()}")


def main():
    """主函数 — 运行所有演示"""
    print("=" * 60)
    print("  Day 11: 自定义工具与记忆系统")
    print("  零 LangChain 依赖 | MCP-native 工具 | 三级记忆")
    print("=" * 60)

    try:
        demo_tools_showcase()
        demo_short_term_memory()
        demo_long_term_memory()
        demo_memory_agent()

        print("\n" + "=" * 60)
        print("  ✅ 所有演示完成！")
        print("=" * 60)
        print("\n  💡 Day 11 关键要点：")
        print("    1. MCP-native 工具类 — 零框架依赖，纯 Python 实现")
        print("    2. 三级记忆 — 工作记忆(任务级) + 短期记忆(会话级) + 长期记忆(持久)")
        print("    3. MemoryAgent — 记忆检索与工具调用的融合")
        print("    4. 长期记忆的 LLM 自动提取 — 无需手动标注")
        print("    5. 所有记忆组件都是独立的、可测试的单元")

    except Exception as e:
        print(f"\n  ❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
