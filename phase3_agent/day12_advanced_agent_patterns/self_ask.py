"""
self_ask.py — Self-Ask 模式实现

Self-Ask 流程：
1. LLM 分析问题 → 是否可以直接回答？
2. 如果不能 → LLM 生成一个子问题（follow-up question）
3. 搜索/计算子问题的答案
4. 将子答案加入上下文 → 回到步骤 1
5. 信息充足时 → 生成最终答案

与 ReAct 的区别：
- Self-Ask 的每一步都是一问一答的形式，更结构化
- 子问题是 LLM 自动生成的，不需要用户参与
- 适合需要层层递进推理的复杂问题
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

from openai import OpenAI
import json
from tools import get_tools_for_patterns, find_tool_by_name


class SelfAskAgent:
    """Self-Ask Agent：通过追问自己来分解复杂问题"""

    def __init__(self, tools=None, max_follow_ups=5):
        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        self.tools = tools if tools is not None else get_tools_for_patterns()
        self.max_follow_ups = max_follow_ups  # 最大追问次数

        self._openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.inputSchema
                }
            }
            for t in self.tools
        ]

    def should_ask_follow_up(self, question: str, context: list) -> tuple:
        """LLM 判断：是否需要追问，以及追问什么"""
        context_text = "\n".join(f"  Q{i+1}: {c['question']}\n  A{i+1}: {c['answer']}"
                                 for i, c in enumerate(context))

        decide_prompt = (
            "你是一个善于自我提问的推理助手。面对一个问题，你需要判断：\n"
            "1. 当前已有的信息是否足够直接回答原问题？\n"
            "2. 如果不够，需要追问什么子问题来获取缺失的信息？\n"
            "3. 如果需要搜索或计算，使用工具获取信息。\n\n"
            "返回 JSON 格式：\n"
            "{\n"
            '  "can_answer": false,  // 是否可以回答原问题\n'
            '  "follow_up": "子问题描述",  // 如果不能回答，追问什么\n'
            '  "need_tool": false,  // 是否需要调用工具\n'
            '  "tool_name": "search",  // 工具名称\n'
            '  "tool_args": {"query": "..."}  // 工具参数\n'
            '  "answer": "..."  // 如果能回答，直接给出答案\n'
            "}"
        )

        messages = [
            {"role": "system", "content": decide_prompt},
            {"role": "user", "content": (
                f"原问题：{question}\n\n"
                f"已知信息：\n{context_text if context_text else '（暂无）'}\n\n"
                f"判断是否可以回答原问题。如果不能，提出一个追问。"
            )}
        ]

        # Tool Calling Loop — 让 LLM 决定是否需要工具
        for _ in range(2):
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=self._openai_tools,
                tool_choice="auto",
                temperature=0.2
            )

            msg = response.choices[0].message

            if not msg.tool_calls:
                data = json.loads(msg.content or "{}")
                return data.get("can_answer", True), data.get("follow_up", ""), data.get("answer", "")

            # 执行工具
            messages.append(msg)
            for tc in msg.tool_calls:
                tool = find_tool_by_name(self.tools, tc.function.name)
                args = json.loads(tc.function.arguments)
                if tool:
                    result = tool.execute(**args)
                    tool_output = result["content"][0]["text"]
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_output
                    })

        # 默认：可以回答
        return True, "", "信息不足，无法回答"

    def run(self, question: str) -> str:
        """运行 Self-Ask Agent"""
        print("  📋 [Self-Ask] 开始处理问题...")
        print(f"  💡 原问题: {question}")

        context = []  # 积累的子问题答案
        follow_up_count = 0

        while follow_up_count < self.max_follow_ups:
            can_answer, follow_up, direct_answer = self.should_ask_follow_up(question, context)

            if can_answer:
                print(f"  ✅ 信息充足，生成答案")
                return direct_answer or self._generate_final_answer(question, context)

            # 需要追问
            follow_up_count += 1
            print(f"\n  ❓ 追问 {follow_up_count}: {follow_up}")

            # 回答追问（可能需要工具）
            answer = self._answer_follow_up(follow_up, context)
            context.append({"question": follow_up, "answer": answer})
            print(f"  💡 回答: {answer[:150]}...")

        # 超出最大追问次数，生成最佳答案
        return self._generate_final_answer(question, context)

    def _answer_follow_up(self, follow_up: str, context: list) -> str:
        """回答一个追问 — 可能需要调用工具"""
        messages = [
            {"role": "system", "content": "你是一个信息检索助手。回答以下问题，必要时使用工具搜索或计算。"},
            {"role": "user", "content": follow_up}
        ]

        for _ in range(3):
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=self._openai_tools,
                tool_choice="auto",
                temperature=0.2
            )

            msg = response.choices[0].message
            if not msg.tool_calls:
                return msg.content or "无法获取信息"

            messages.append(msg)
            for tc in msg.tool_calls:
                tool = find_tool_by_name(self.tools, tc.function.name)
                args = json.loads(tc.function.arguments)
                if tool:
                    result = tool.execute(**args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result["content"][0]["text"]
                    })

        return "未能获取到足够信息"

    def _generate_final_answer(self, original_question: str, context: list) -> str:
        """基于所有追问的答案，生成最终答案"""
        context_text = "\n".join(
            f"追问{i+1}: {c['question']}\n回答{i+1}: {c['answer']}"
            for i, c in enumerate(context)
        )

        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "基于收集到的信息，给出准确、完整的答案。"},
                {"role": "user", "content": (
                    f"原问题：{original_question}\n\n"
                    f"收集到的信息：\n{context_text}\n\n"
                    f"请用流畅的中文给出最终答案。"
                )}
            ],
            temperature=0.5
        )

        return response.choices[0].message.content or "无法生成答案"


def demo_self_ask():
    """演示 Self-Ask 模式"""
    print("\n" + "=" * 60)
    print("  Self-Ask 模式演示")
    print("=" * 60)

    agent = SelfAskAgent()

    # 需要层层递进推理的问题
    task = "苹果公司的现任CEO是谁？请告诉我关于他的出生地和教育背景"

    print(f"\n  🎯 问题: {task}\n")
    try:
        result = agent.run(task)
        print(f"\n  ✅ 最终答案:\n{result}")
    except Exception as e:
        print(f"\n  ❌ 执行出错: {e}")


if __name__ == "__main__":
    demo_self_ask()
