"""
first_llm_call.py
第一个LLM API调用 — 同时演示原始HTTP方式和openai SDK方式

功能：
1. 原始HTTP请求调用LLM API（理解底层协议）
2. openai SDK调用LLM API（生产推荐方式）
3. 流式输出（streaming）
4. 多轮对话
5. 参数调节（temperature/max_tokens对比）

学习目标：
1. 掌握openai SDK的基本用法
2. 理解API请求的底层结构
3. 学会处理API错误
4. 了解不同参数对输出的影响
"""
import sys
from pathlib import Path
# 将项目根目录加入sys.path，以便导入config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL  # 从共享配置导入
from openai import OpenAI  # openai SDK，兼容所有支持OpenAI协议的API
import requests  # 用于演示原始HTTP方式
import json  # JSON序列化
import time  # 计时


# ==================== 初始化OpenAI客户端 ====================

# 创建OpenAI客户端实例，所有API调用都通过这个客户端进行
client = OpenAI(
    api_key=OPENAI_API_KEY,  # API密钥（从.env文件加载）
    base_url=OPENAI_BASE_URL  # API地址（支持DeepSeek/NVIDIA/OpenAI等）
)

print(f"🔧 当前配置:")
print(f"   模型: {OPENAI_MODEL}")
print(f"   地址: {OPENAI_BASE_URL}")


# ==================== 第1部分：原始HTTP方式调用API ====================

def call_via_http(prompt: str) -> str:
    """
    用原始HTTP请求调用LLM API
    理解底层协议很有价值：调试、不依赖SDK、了解API的JSON结构
    """
    # 构建请求头 — Content-Type和Authorization是必须的
    headers = {
        "Content-Type": "application/json",  # 告诉服务器发送的是JSON
        "Authorization": f"Bearer {OPENAI_API_KEY}"  # Bearer Token认证
    }

    # 构建请求体 — 这就是发给LLM的完整指令
    payload = {
        "model": OPENAI_MODEL,  # 指定模型
        "messages": [  # 消息列表（最核心的字段！）
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,  # 创造性参数
        "max_tokens": 512  # 最大输出token数
    }

    # 发送POST请求
    response = requests.post(
        f"{OPENAI_BASE_URL}/chat/completions",  # API端点
        headers=headers,
        json=payload,  # requests自动将dict序列化为JSON
        timeout=30  # 30秒超时
    )
    response.raise_for_status()  # 非2xx状态码会抛出HTTPError

    # 解析响应 — 标准的Chat Completion格式
    result = response.json()
    # 响应结构: {"choices": [{"message": {"content": "..."}}], "usage": {...}}
    content = result["choices"][0]["message"]["content"]
    return content


# ==================== 第2部分：openai SDK方式调用API（推荐）====================

def call_via_sdk(prompt: str, temperature: float = 0.7) -> str:
    """
    用openai SDK调用LLM API — 更简洁、有类型提示、自动重试
    这是本课程后续所有代码采用的统一方式
    """
    # SDK封装了HTTP细节，直接传递参数即可
    response = client.chat.completions.create(
        model=OPENAI_MODEL,  # 模型名称
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,  # 创造度（0=确定，1=创造）
        max_tokens=512  # 最大输出长度
    )
    # response是Pydantic模型，有完整的类型提示和IDE补全
    content = response.choices[0].message.content
    return content


# ==================== 第3部分：带System消息的调用 ====================

def call_with_system(system_prompt: str, user_message: str) -> str:
    """
    使用System消息设定AI的角色和行为
    System消息是最重要的上下文 — 它定义了AI的"人设"
    """
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},  # System=给AI定规矩
            {"role": "user", "content": user_message}  # User=用户的具体问题
        ],
        temperature=0.7,
        max_tokens=512
    )
    return response.choices[0].message.content


# ==================== 第4部分：流式输出 ====================

def demo_streaming(prompt: str):
    """
    演示流式输出 — 边生成边打印，像ChatGPT打字效果
    用户体验更好，不用等完整回复
    """
    print(f"\n用户: {prompt}")
    print("AI: ", end="", flush=True)  # flush=True立即输出，不缓冲

    # stream=True启用流式输出
    stream = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=256,
        stream=True  # 开启流式输出
    )

    # 逐块接收并打印
    for chunk in stream:
        # 每个chunk包含一小段生成的文字（delta）
        if chunk.choices and chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="", flush=True)  # 逐字打印

    print()  # 最后换行


# ==================== 第5部分：多轮对话 ====================

def demo_multi_turn():
    """
    演示多轮对话 — 保存完整的对话历史传给LLM
    LLM本身是无状态的，每次请求都需要带上全部历史
    """
    print("\n" + "=" * 50)
    print("多轮对话演示")
    print("-" * 50)

    # messages列表保存完整对话历史
    messages = [
        {"role": "system", "content": "你是一个简洁的助手，回答不超过2句话。"}
    ]

    questions = [
        "什么是Python？",
        "它有什么优点？",  # LLM需要记住上一轮在讨论Python
        "再举一个简单的代码例子",
    ]

    for q in questions:
        # 添加用户消息
        messages.append({"role": "user", "content": q})

        # 发送完整历史
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,  # 每次都发送完整的对话历史
            temperature=0.7,
            max_tokens=256
        )

        answer = response.choices[0].message.content if response.choices else "（无回复）"

        # 添加AI回复到历史中
        if response.choices:
            messages.append({"role": "assistant", "content": answer})

        print(f"\n👤: {q}")
        print(f"🤖: {answer}")

    print(f"\n📊 对话共 {len(messages)} 条消息（含system）")


# ==================== 第6部分：参数调节对比 ====================

def demo_parameters():
    """
    演示temperature和max_tokens对输出的影响
    """
    print("\n" + "=" * 50)
    print("参数对比演示")
    print("-" * 50)

    prompt = "请用一句话介绍Python编程语言"

    # 对比不同temperature
    print("\n💡 Temperature 参数说明：")
    print("   0.1-0.3: 非常保守、确定性高")
    print("   0.5-0.7: 平衡、自然流畅（推荐）")
    print("   0.8-1.0: 更有创意、多样化")
    print("   >1.2: 可能产生混乱或无意义的输出\n")
    
    for temp in [0.1, 0.7, 1.5]:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temp,
            max_tokens=256,
            seed=42  # 固定随机种子，让结果可复现
        )
        # 显示token用量
        usage = response.usage
        print(f"\ntemperature={temp} (tokens: {usage.total_tokens}):")
        print(f"  {response.choices[0].message.content}")

    # 对比不同max_tokens
    print(f"\n--- max_tokens对比 ---")
    for mt in [30, 100, 256]:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": "请详细介绍深度学习"}],
            temperature=0.7,
            max_tokens=mt,
            seed=42
        )
        content = response.choices[0].message.content
        print(f"\nmax_tokens={mt} (实际长度: {len(content)}字):")
        print(f"  {content[:100]}{'...' if len(content) > 100 else ''}")


def main():
    """主函数 — 按顺序演示所有功能"""
    print("=" * 60)
    print("Day 06: 第一个LLM API调用")
    print("=" * 60)

    try:
        # 第1部分：原始HTTP方式
        print("\n📋 1. 原始HTTP方式调用:")
        print("-" * 40)
        response = call_via_http("请用一句话介绍你自己")
        print(f"HTTP方式: {response}")

        # 第2部分：SDK方式
        print("\n📋 2. openai SDK方式调用（推荐）:")
        print("-" * 40)
        response = call_via_sdk("请用一句话介绍Python")
        print(f"SDK方式: {response}")

        # 第3部分：带System消息
        print("\n📋 3. 带System消息的调用 — 角色设定:")
        print("-" * 40)
        # 角色1：诗人
        poet_response = call_with_system(
            "你是一位中国古代诗人，用文言文风格回复。",
            "今天天气很好"
        )
        print(f"诗人风格: {poet_response}")

        # 角色2：程序员
        coder_response = call_with_system(
            "你是一个Python编程专家，回复简洁专业，给出可执行代码。",
            "如何读取CSV文件？"
        )
        print(f"程序员风格: {coder_response}")

        # 第4部分：流式输出
        print("\n📋 4. 流式输出:")
        print("-" * 40)
        demo_streaming("用3句话介绍深度学习")

        # 第5部分：多轮对话
        demo_multi_turn()

        # 第6部分：参数对比
        demo_parameters()

        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        print("=" * 60)
        print("\n💡 提示：后续课程全部使用openai SDK方式，简洁且生产可用")

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        print("\n常见问题排查:")
        print("  1. 检查 .env 文件中 OPENAI_API_KEY 是否正确")
        print("  2. 检查网络连接是否正常")
        print("  3. 检查 API Key 是否还有余额")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()