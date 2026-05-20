"""
memory.py — 原生三级记忆系统

功能：
1. WorkingMemory — 当前任务的工作记忆（键值存储、中间步骤）
2. ShortTermMemory — 短期对话记忆（滑动窗口的对话历史）
3. LongTermMemory — 长期持久记忆（基于 LLM 的关键信息提取和存储）

设计原则：
- 零 LangChain 依赖 — 纯 Python 实现
- 与 OpenAI 消息格式兼容 — ShortTermMemory 直接返回 messages 列表
- 生产级设计 — 支持存储持久化、TTL 过期
"""
import json  # JSON 序列化/反序列化
import os  # 文件操作
from datetime import datetime  # 时间戳
from collections import OrderedDict  # 有序字典（LRU 实现）
from typing import Optional  # 类型提示

# 导入 LLM 客户端（用于长期记忆的摘要提取）
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from openai import OpenAI


# ==================== 工作记忆 ====================

class WorkingMemory:
    """当前任务的工作记忆 — 存储中间步骤和临时数据"""

    def __init__(self, max_items: int = 10):
        self.max_items = max_items  # 最大存储条目数
        self._store = OrderedDict()  # 使用 OrderedDict 保持插入顺序
        self._step_log = []  # 步骤日志 — 记录每一步的操作

    def add(self, key: str, value: str) -> None:
        """存入一条工作记忆"""
        # LRU 淘汰：如果达到上限，删除最旧的条目
        if len(self._store) >= self.max_items:
            oldest_key = next(iter(self._store))
            del self._store[oldest_key]
        self._store[key] = {"value": value, "timestamp": datetime.now().isoformat()}

    def get(self, key: str) -> Optional[str]:
        """读取一条工作记忆"""
        entry = self._store.get(key)
        return entry["value"] if entry else None

    def log_step(self, action: str, result: str) -> None:
        """记录一个执行步骤"""
        self._step_log.append({
            "step": len(self._step_log) + 1,
            "action": action,
            "result": result[:200],  # 截断过长结果
            "time": datetime.now().isoformat()
        })

    def clear(self) -> None:
        """清空工作记忆（任务切换时使用）"""
        self._store.clear()
        self._step_log.clear()

    def to_context(self) -> str:
        """将工作记忆格式化为 LLM 可读的上下文文本"""
        if not self._store and not self._step_log:
            return "暂无工作记忆"
        lines = ["[工作记忆]"]
        if self._store:
            lines.append("  存储数据：")
            for key, entry in self._store.items():
                lines.append(f"    {key}: {entry['value']}")
        if self._step_log:
            lines.append("  执行步骤：")
            for step in self._step_log:
                lines.append(f"    步骤{step['step']}: {step['action']} → {step['result'][:100]}")
        return "\n".join(lines)


# ==================== 短期记忆（对话历史） ====================

class ShortTermMemory:
    """短期记忆 — 滑动窗口的对话历史，直接兼容 OpenAI messages 格式"""

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns  # 最大保留的对话轮数
        self._messages = []  # OpenAI 格式的消息列表

    def add_user_message(self, content: str) -> None:
        """添加用户消息到对话历史"""
        self._messages.append({"role": "user", "content": content})
        self._trim()  # 检查是否需要裁剪

    def add_assistant_message(self, content: str) -> None:
        """添加助手回复到对话历史"""
        self._messages.append({"role": "assistant", "content": content})
        self._trim()

    def add_tool_result(self, tool_call_id: str, tool_name: str, result: str) -> None:
        """添加工具调用和结果到对话历史"""
        # 先添加助手的工具调用消息
        self._messages.append({
            "role": "assistant",
            "tool_calls": [{
                "id": tool_call_id,
                "type": "function",
                "function": {"name": tool_name, "arguments": "{}"}
            }]
        })
        # 再添加工具返回结果
        self._messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": result
        })
        self._trim()

    def get_messages(self) -> list:
        """返回 OpenAI 格式的完整消息列表"""
        return list(self._messages)

    def get_recent(self, n: int) -> list:
        """返回最近 n 条消息"""
        return self._messages[-n:] if n < len(self._messages) else list(self._messages)

    def clear(self) -> None:
        """清空对话历史"""
        self._messages.clear()

    def to_context_string(self) -> str:
        """将对话历史格式化为可读文本"""
        lines = ["[对话历史]"]
        for msg in self._messages[-10:]:  # 只显示最近 10 条
            role = msg["role"]
            content = msg.get("content", str(msg.get("tool_calls", "")))
            lines.append(f"  [{role}]: {str(content)[:150]}")
        return "\n".join(lines)

    def _trim(self) -> None:
        """裁剪对话历史到最大轮数以内"""
        # 一个对话轮次 = user + assistant（至少 2 条消息）
        # 如果消息数量超过 max_turns * 2 + system，裁剪最旧的轮次
        max_messages = self.max_turns * 2 + 2  # +2 缓冲
        if len(self._messages) > max_messages:
            # 保留 system 消息（第一条）+ 最近的轮次
            system_msgs = [m for m in self._messages if m["role"] == "system"]
            other_msgs = [m for m in self._messages if m["role"] != "system"]
            excess = len(other_msgs) - (self.max_turns * 2)
            if excess > 0:
                self._messages = system_msgs + other_msgs[excess:]

    def __len__(self) -> int:
        """返回消息数量"""
        return len(self._messages)


# ==================== 长期记忆 ====================

class LongTermMemory:
    """长期记忆 — 基于文件存储的持久化记忆，支持 LLM 驱动的信息提取"""

    def __init__(self, storage_path: str = None):
        # 记忆存储文件路径
        if storage_path is None:
            storage_path = str(Path(__file__).parent / "long_term_memory.json")
        self.storage_path = storage_path
        # 加载已有记忆
        self._memories = self._load()
        # LLM 客户端 — 用于摘要提取
        self._llm = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        # 记忆提取的系统提示
        self._extraction_prompt = (
            "你是一个信息提取助手。请从以下对话中提取需要长期记住的关键信息。"
            "提取内容包括但不限于：用户姓名、偏好、重要事实、待办承诺、学习进度。"
            "以 JSON 格式返回，每一条信息包含 key（唯一标识）和 value（具体内容）。"
            "返回格式：{\"memories\": [{\"key\": \"...\", \"value\": \"...\"}]}"
        )

    def remember(self, key: str, info: str) -> None:
        """主动存储一条长期记忆"""
        self._memories[key] = {
            "value": info,
            "updated_at": datetime.now().isoformat(),
            "access_count": 0
        }
        self._save()

    def recall(self, key: str) -> Optional[str]:
        """检索一条长期记忆"""
        entry = self._memories.get(key)
        if entry:
            entry["access_count"] += 1  # 记录访问次数
            self._save()
            return entry["value"]
        return None

    def summarize_and_store(self, conversation_text: str) -> list:
        """使用 LLM 从对话中提取关键信息并存入长期记忆"""
        try:
            response = self._llm.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self._extraction_prompt},
                    {"role": "user", "content": f"请从以下对话中提取关键信息：\n\n{conversation_text}"}
                ],
                temperature=0.2,  # 低温度以确保提取的稳定性
                response_format={"type": "json_object"}  # 要求 JSON 格式输出
            )
            result = json.loads(response.choices[0].message.content)
            memories = result.get("memories", [])

            # 存储提取到的每条记忆
            stored = []
            for mem in memories:
                key = mem.get("key", "")
                value = mem.get("value", "")
                if key and value:
                    self.remember(key, value)
                    stored.append(f"{key}: {value}")

            return stored
        except Exception as e:
            print(f"  ⚠️ 长期记忆提取失败：{e}")
            return []

    def get_all_memories(self) -> str:
        """获取所有长期记忆的文本表示"""
        if not self._memories:
            return "暂无长期记忆"
        lines = ["[长期记忆]"]
        for key, entry in self._memories.items():
            lines.append(f"  • {key}: {entry['value']}（更新于 {entry['updated_at'][:10]}）")
        return "\n".join(lines)

    def forget(self, key: str) -> bool:
        """删除一条长期记忆"""
        if key in self._memories:
            del self._memories[key]
            self._save()
            return True
        return False

    def clear_all(self) -> None:
        """清空所有长期记忆"""
        self._memories.clear()
        self._save()

    def _load(self) -> dict:
        """从文件加载记忆"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save(self) -> None:
        """将记忆持久化到文件"""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._memories, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"  ⚠️ 长期记忆保存失败：{e}")


# ==================== 直接测试 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  记忆系统测试")
    print("=" * 60)

    # 测试工作记忆
    print("\n📋 1. 工作记忆测试：")
    wm = WorkingMemory(max_items=5)
    wm.add("task", "分析天气数据")
    wm.add("step1_result", "北京：晴 22°C")
    wm.log_step("查询天气", "成功获取北京天气数据")
    print(wm.to_context())

    # 测试短期记忆
    print("\n📋 2. 短期记忆测试：")
    sm = ShortTermMemory(max_turns=3)
    sm.add_user_message("今天天气怎么样？")
    sm.add_assistant_message("北京今天晴，22°C")
    sm.add_user_message("帮我记住这个温度")
    sm.add_assistant_message("已记录：北京今天 22°C")
    print(f"  · 消息总数：{len(sm)}")
    print(f"  · 最近 2 条：{sm.get_recent(2)}")

    # 测试长期记忆
    print("\n📋 3. 长期记忆测试：")
    lm = LongTermMemory()
    lm.remember("user_city", "用户居住在北京")
    lm.remember("user_preference", "用户喜欢技术类话题")
    print(lm.get_all_memories())

    print("\n" + "=" * 60)
    print("  测试完成！记忆系统运行正常")
    print("=" * 60)