"""
communication.py — Agent 间通信机制

三种通信模式：
1. DirectMessenger — 点对点消息传递（邮箱模式）
2. SharedBlackboard — 共享黑板（键值存储，多 Agent 读写）
3. PubSubSystem — 发布订阅事件系统

设计原则：零外部依赖，纯 Python 数据结构，同步操作
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Callable


# ==================== 消息数据类 ====================

@dataclass
class Message:
    """Agent 间通信的消息"""
    sender: str       # 发送者名称
    receiver: str     # 接收者名称
    content: str      # 消息内容
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ==================== 点对点消息传递 ====================

class DirectMessenger:
    """直接消息传递 — 基于邮箱的点对点通信"""

    def __init__(self):
        self._mailboxes: Dict[str, List[Message]] = {}  # 接收者 → 消息列表

    def send(self, message: Message) -> None:
        """发送消息到接收者的邮箱"""
        if message.receiver not in self._mailboxes:
            self._mailboxes[message.receiver] = []
        self._mailboxes[message.receiver].append(message)

    def receive(self, receiver: str) -> List[Message]:
        """接收者收取所有未读消息（收取后清空邮箱）"""
        messages = self._mailboxes.get(receiver, [])
        self._mailboxes[receiver] = []  # 清空已读消息
        return messages

    def has_messages(self, receiver: str) -> bool:
        """检查是否有未读消息"""
        return bool(self._mailboxes.get(receiver))


# ==================== 共享黑板 ====================

class SharedBlackboard:
    """共享黑板 — 多 Agent 共享的键值存储空间"""

    def __init__(self):
        self._data: Dict[str, dict] = {}  # key → {value, writer, timestamp}

    def write(self, key: str, value: str, writer: str = "unknown") -> None:
        """写入数据到黑板"""
        self._data[key] = {
            "value": value,
            "writer": writer,
            "timestamp": datetime.now().isoformat()
        }

    def read(self, key: str) -> dict:
        """读取指定键的数据"""
        return self._data.get(key, None)

    def get_all_data(self) -> Dict[str, dict]:
        """获取黑板上所有数据"""
        return dict(self._data)

    def display(self) -> str:
        """展示黑板上的所有内容"""
        if not self._data:
            return "[黑板为空]"
        lines = [f"{'='*40}", "  共享黑板内容", f"{'='*40}"]
        for key, entry in self._data.items():
            lines.append(f"  [{key}] ← {entry['writer']}")
            lines.append(f"    {entry['value'][:200]}")
            lines.append(f"    {entry['timestamp']}")
        return "\n".join(lines)

    def clear(self) -> None:
        """清空黑板"""
        self._data.clear()


# ==================== 发布订阅系统 ====================

class PubSubSystem:
    """发布订阅事件系统 — 按主题广播消息"""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}  # 主题 → 回调函数列表

    def subscribe(self, topic: str, callback: Callable) -> None:
        """订阅一个主题"""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)
        print(f"  📡 订阅: [{topic}] ← {getattr(callback, '__name__', str(callback))}")

    def unsubscribe(self, topic: str, callback: Callable) -> bool:
        """取消订阅"""
        if topic in self._subscribers and callback in self._subscribers[topic]:
            self._subscribers[topic].remove(callback)
            return True
        return False

    def publish(self, topic: str, message: str) -> int:
        """向订阅者发布消息，返回接收消息的订阅者数量"""
        if topic not in self._subscribers:
            return 0
        count = 0
        for callback in self._subscribers[topic]:
            try:
                callback(message)
                count += 1
            except Exception as e:
                print(f"  ⚠️ 订阅者回调失败: {e}")
        return count

    def get_topics(self) -> list:
        """获取所有主题"""
        return list(self._subscribers.keys())

    def get_subscriber_count(self, topic: str) -> int:
        """获取某主题的订阅者数量"""
        return len(self._subscribers.get(topic, []))


# ==================== 直接测试 ====================

if __name__ == "__main__":
    print("=" * 50)
    print("  通信机制测试")
    print("=" * 50)

    # 测试直接消息
    print("\n📨 1. DirectMessenger 测试:")
    dm = DirectMessenger()
    dm.send(Message(sender="AgentA", receiver="AgentB", content="你好，请处理任务"))
    dm.send(Message(sender="AgentA", receiver="AgentB", content="任务状态如何？"))
    msgs = dm.receive("AgentB")
    for m in msgs:
        print(f"    {m.sender} → {m.receiver}: {m.content}")

    # 测试黑板
    print("\n📋 2. SharedBlackboard 测试:")
    board = SharedBlackboard()
    board.write("task_status", "任务完成 80%", writer="Worker1")
    board.write("result", "分析结果：正相关性", writer="Worker2")
    print(board.display())

    # 测试发布订阅
    print("\n📡 3. PubSubSystem 测试:")

    def on_task_complete(msg):
        print(f"    [回调] 收到任务完成通知: {msg}")

    def on_error(msg):
        print(f"    [回调] 收到错误通知: {msg}")

    ps = PubSubSystem()
    ps.subscribe("task.complete", on_task_complete)
    ps.subscribe("task.error", on_error)
    ps.publish("task.complete", "研究报告已生成")
    ps.publish("task.error", "数据格式错误")
