"""
Day19: 对话式 RAG（Conversation RAG）— 支持多轮对话的检索增强生成

核心挑战:
1. 多轮对话中，用户的后续问题可能省略上下文（如 "那个作者是谁?"）
2. 需要把对话历史纳入考虑，确保检索的准确性和回答的连贯性
3. 需要判断何时触发检索（简单寒暄不需要检索文档）

解决方案:
1. 查询重写（Query Rewriting）: 结合历史上下文，将简略问句改写为完整的检索查询
2. 检索门控（Retrieval Gating）: 判断用户消息是否需要检索知识库
3. 会话管理: 维护每个 session 的对话历史，支持多会话并发
"""

import sys
from pathlib import Path
import os
from typing import Any

# ==================== 导入公共配置 ====================
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # 将项目根目录加入 sys.path
from config import (  # 从公共配置导入所需变量
    OPENAI_API_KEY,    # API 密钥
    OPENAI_BASE_URL,   # API 请求地址
    OPENAI_MODEL,      # 大模型名称
    HF_ENDPOINT,       # HuggingFace 镜像地址（国内加速）
)

from openai import OpenAI  # OpenAI 兼容客户端
import chromadb  # 向量数据库，用于存储和检索知识文档


# ==================== 小型知识库构建工具 ====================
def build_knowledge_base(documents: list[str]) -> chromadb.Collection:
    """
    根据文档列表构建 ChromaDB 知识库（向量化存储）

    参数:
        documents: 要存入知识库的文档文本列表

    返回:
        ChromaDB Collection 对象，可用于检索
    """
    # 设置 HuggingFace 镜像端点（在导入向量模型前必须设置）
    os.environ["HF_ENDPOINT"] = HF_ENDPOINT
    from sentence_transformers import SentenceTransformer  # 延迟导入

    # 加载嵌入模型
    embedding_model: SentenceTransformer = SentenceTransformer(
        "BAAI/bge-small-zh-v1.5"  # 中文小模型，性价比优秀
    )

    # 定义自定义嵌入函数：接收文档列表，返回向量列表
    class LocalEmbedding:
        """包装本地 SentenceTransformer 为 ChromaDB 兼容的嵌入函数"""
        def __call__(self, texts: list[str]) -> list[list[float]]:
            # 对每个文本进行向量编码，返回浮点数列表的列表
            embeddings: list = embedding_model.encode(texts).tolist()
            return embeddings  # shape: (len(texts), embedding_dim)

    # 创建 ChromaDB 内存客户端（无需持久化存储）
    client: chromadb.Client = chromadb.Client()

    # 创建或获取 collection，指定使用自定义嵌入函数
    collection: chromadb.Collection = client.create_collection(
        name="conversation_kb",                      # Collection 名称
        embedding_function=LocalEmbedding(),          # 使用本地嵌入模型
    )

    # 批量添加文档到知识库
    for idx, doc in enumerate(documents):
        collection.add(
            documents=[doc],                          # 文档文本内容
            ids=[f"doc_{idx}"],                       # 唯一 ID
            metadatas=[{"source": f"doc_{idx}"}],     # 元数据（来源信息）
        )

    print(f"知识库构建完成: {len(documents)} 篇文档已入库")
    return collection  # 返回可检索的 collection


# ==================== 对话式 RAG 系统 ====================
class ConversationRAG:
    """
    对话式 RAG — 支持多轮对话的检索增强生成系统

    核心功能:
    1. 会话管理: 每个 session_id 独立维护对话历史
    2. 查询重写: 将省略了上下文的指代消解为完整的检索查询
    3. 检索门控: 判断消息是否需要从知识库检索
    4. 带上下文回答: 将历史 + 检索结果一起喂给 LLM 生成回答
    """

    def __init__(self, knowledge_base: chromadb.Collection) -> None:
        """
        初始化对话式 RAG 系统

        参数:
            knowledge_base: ChromaDB collection，用于文档检索
        """
        # 初始化 LLM 客户端
        self.client: OpenAI = OpenAI(
            api_key=OPENAI_API_KEY,     # API 密钥
            base_url=OPENAI_BASE_URL,   # API 地址
        )
        # 知识库引用
        self.knowledge_base: chromadb.Collection = knowledge_base  # 知识库 collection
        # 会话存储: {session_id: [message_dict, ...]}
        self.sessions: dict[str, list[dict[str, str]]] = {}  # 多会话对话历史管理
        # 每轮检索返回的文档数量
        self.retrieve_k: int = 3  # 默认检索 Top-3

    # ----------------------------------------------------------------
    def _should_retrieve(self, message: str) -> bool:
        """
        检索门控 — 判断当前消息是否需要从知识库检索

        使用 LLM 判断: 简单的寒暄/闲聊不需要检索，
        需要知识/信息的查询才触发检索

        参数:
            message: 用户输入消息

        返回:
            True 表示需要检索，False 表示不需要
        """
        # 使用 LLM 判断是否需要进行知识检索
        gate_prompt: str = f"""判断以下用户消息是否需要从知识库中检索信息。
如果消息是简单问候、闲聊或个人情感表达，回答 "NO"。
如果消息在询问事实、知识或需要信息支撑，回答 "YES"。

用户消息: "{message}"

需要检索吗？(YES/NO):"""

        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": gate_prompt}],
            temperature=0.0,   # 零温度确保一致性
            max_tokens=5,      # YES/NO 两个字母足够
        )
        verdict: str = response.choices[0].message.content.strip().upper()
        return "YES" in verdict  # 如果 LLM 回答 YES，则触发检索

    # ----------------------------------------------------------------
    def _build_search_query(self, message: str, history: list[dict[str, str]]) -> str:
        """
        查询重写 — 结合对话历史，将简略问句扩展为完整的检索查询

        举例:
        - 用户先问 "ChromaDB 是什么?"
        - 接着问 "它的性能如何?"
        - 重写后: "ChromaDB 的性能如何?"

        参数:
            message: 用户当前消息（可能省略了上下文）
            history: 该会话的对话历史记录列表

        返回:
            重写后的完整检索查询字符串
        """
        if not history:
            return message  # 没有历史则直接使用原始消息

        # 格式化历史对话为文本（最近 6 轮就足够）
        # 取最近 6 轮（3 组问答），避免历史过长
        recent_history: list[dict[str, str]] = history[-6:]  # 最多取最近 3 组对话

        # 将历史转为可读文本
        history_text: str = ""
        for h in recent_history:
            role: str = "用户" if h["role"] == "user" else "助手"  # 角色名中文化
            history_text += f"{role}: {h['content']}\n"

        # 构造重写提示词
        rewrite_prompt: str = f"""你是一个查询重写助手。请根据对话历史，将用户的当前消息重写为一个完整的、独立的检索查询。

对话历史:
{history_text}

用户当前消息: {message}

请输出重写后的检索查询（一句话）:"""

        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": rewrite_prompt}],
            temperature=0.0,       # 重写应保持稳定
        )
        rewritten: str = response.choices[0].message.content.strip()  # 获取重写结果
        return rewritten  # 返回重写后的查询

    # ----------------------------------------------------------------
    def _retrieve(self, query: str, k: int | None = None) -> list[str]:
        """
        从知识库检索相关文档

        参数:
            query: 检索查询（可能是重写后的）
            k: 返回文档数量，默认使用 self.retrieve_k

        返回:
            检索到的文档文本列表
        """
        if k is None:
            k = self.retrieve_k  # 使用默认的检索数量
        # 调用 ChromaDB 的 query 方法进行语义检索
        results = self.knowledge_base.query(query_texts=[query], n_results=k)
        # 提取文档文本列表
        docs: list[str] = results["documents"][0] if results["documents"] else []
        return docs  # 返回文档文本列表

    # ----------------------------------------------------------------
    def _generate_answer(
        self,
        user_message: str,
        retrieved_docs: list[str],
        history: list[dict[str, str]],
    ) -> str:
        """
        基于历史上下文和检索结果，用 LLM 生成回答

        参数:
            user_message: 用户的当前消息
            retrieved_docs: 检索到的相关文档
            history: 对话历史

        返回:
            LLM 生成的回答文本
        """
        # 构建系统提示词（说明角色和使用文档的原则）
        system_prompt: str = """你是一个智能问答助手。请根据提供的参考文档和对话历史回答用户的问题。

规则:
1. 如果参考文档包含了相关信息，请基于文档回答
2. 如果文档信息不足以回答，请如实说明
3. 保持回答与对话历史的连贯性
4. 回答简洁清晰，避免过度冗长"""

        # 构建对话消息列表
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        # 加入最近的历史对话（最多 6 条）
        recent_history: list[dict[str, str]] = history[-6:] if history else []
        for h in recent_history:
            messages.append({"role": h["role"], "content": h["content"]})  # 添加历史消息

        # 构建检索文档上下文
        context_text: str = ""
        if retrieved_docs:
            # 将检索文档编号并拼接
            context_parts: list[str] = []
            for i, doc in enumerate(retrieved_docs, 1):
                context_parts.append(f"[文档{i}]\n{doc}")  # 给每个文档编号
            context_text = "\n\n".join(context_parts)

            # 将文档作为参考信息插入用户消息中
            augmented_message: str = f"""参考文档:
{context_text}

用户问题: {user_message}

请基于参考文档回答。"""
            messages.append({"role": "user", "content": augmented_message})
        else:
            # 无检索结果时直接传递用户消息
            messages.append({"role": "user", "content": user_message})

        # 调用 LLM 生成回答
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.7,    # 适度的创造性
            max_tokens=1024,    # 回答最大长度
        )
        return response.choices[0].message.content.strip()  # 返回回答文本

    # ----------------------------------------------------------------
    def chat(self, user_message: str, session_id: str = "default") -> str:
        """
        处理用户消息的核心方法 — 支持多轮对话的完整 RAG 流程

        流程:
        1. 存储用户消息到会话历史
        2. 检索门控: 判断是否需要检索
        3. 如需检索: 查询重写 -> 检索文档 -> 生成回答
        4. 如不需检索: 直接用历史生成回答

        参数:
            user_message: 用户的当前消息
            session_id: 会话 ID（默认为 "default"），不同 ID 隔离对话

        返回:
            助手回答文本
        """
        # ---- 第 1 步: 获取或初始化会话历史 ----
        if session_id not in self.sessions:
            self.sessions[session_id] = []  # 新会话：创建空历史列表

        history: list[dict[str, str]] = self.sessions[session_id]  # 当前会话历史

        # 将用户消息追加到历史
        history.append({"role": "user", "content": user_message})  # 记录用户消息

        # ---- 第 2 步: 检索门控 ----
        need_retrieve: bool = self._should_retrieve(user_message)  # 判断是否需要检索

        # ---- 第 3 步: 根据门控结果执行检索或直接回答 ----
        if need_retrieve:
            # 3a. 查询重写: 将依赖上下文的消息补全
            # 注意: 传入的是重写前的历史（不包含当前消息）
            history_before = history[:-1]  # 当前消息之前的历史
            search_query: str = self._build_search_query(user_message, history_before)
            print(f"  [检索触发] 原始: '{user_message}' -> 重写: '{search_query}'")

            # 3b. 执行检索
            retrieved_docs: list[str] = self._retrieve(search_query)
            print(f"  [检索结果] 返回 {len(retrieved_docs)} 篇文档")

            # 3c. 基于检索结果生成回答
            answer: str = self._generate_answer(user_message, retrieved_docs, history_before)
        else:
            # 无需检索: 直接用历史生成回答（不传入检索结果）
            print(f"  [无需检索] 直接对话回答")
            history_before = history[:-1]
            answer = self._generate_answer(user_message, [], history_before)

        # ---- 第 4 步: 将助手回答加入历史 ----
        history.append({"role": "assistant", "content": answer})  # 记录助手回答

        return answer  # 返回回答

    # ----------------------------------------------------------------
    def clear_session(self, session_id: str) -> None:
        """
        清除指定会话的对话历史

        参数:
            session_id: 要清除的会话 ID
        """
        if session_id in self.sessions:
            del self.sessions[session_id]  # 从字典中删除该会话
            print(f"会话 {session_id} 已清除")
        else:
            print(f"会话 {session_id} 不存在，无需清除")

    # ----------------------------------------------------------------
    def get_history(self, session_id: str = "default") -> list[dict[str, str]]:
        """
        获取指定会话的对话历史（用于检查和展示）

        参数:
            session_id: 会话 ID

        返回:
            该会话的对话历史列表
        """
        return self.sessions.get(session_id, [])  # 返回历史，不存在则返回空列表


# ==================== 模块自测代码 ====================
if __name__ == "__main__":
    """
    自测代码: 构建小型知识库，测试多轮对话 RAG 功能
    """
    print("=== 对话式 RAG 模块自测 ===\n")

    # ---- 构建小型测试知识库 ----
    test_docs: list[str] = [
        "Python 是一种解释型、面向对象的高级编程语言，由 Guido van Rossum 于 1991 年发布。Python 的设计哲学强调代码的可读性和简洁性。",
        "LangChain 是一个用于构建 LLM 应用的框架，支持链式调用、Agent、RAG 等功能。它目前的稳定版本是 0.2.x。",
        "ChromaDB 是一个开源的向量数据库，专门为 AI 应用设计。它支持嵌入向量的存储和语义搜索，并且使用非常简单。",
        "RAG（检索增强生成）是一种将信息检索与文本生成相结合的技术。它先从外部知识库中检索相关文档，再让 LLM 基于这些文档生成回答。",
        "LlamaIndex 是另一个 RAG 框架，专注于数据的索引和检索。它提供了丰富的数据连接器和索引结构。",
    ]

    kb: chromadb.Collection = build_knowledge_base(test_docs)  # 构建知识库
    rag: ConversationRAG = ConversationRAG(knowledge_base=kb)  # 初始化对话 RAG

    # ---- 测试简单对话（无需检索） ----
    print("\n--- 第 1 轮: 简单问候（无需检索） ---")
    response1: str = rag.chat("你好！今天天气不错。")
    print(f"助手: {response1}")

    # ---- 测试知识查询（需要检索） ----
    print("\n--- 第 2 轮: 知识查询（触发检索） ---")
    response2: str = rag.chat("什么是 RAG？")
    print(f"助手: {response2}")

    # ---- 测试上下文依赖问题（需要查询重写） ----
    print("\n--- 第 3 轮: 上下文依赖（测试查询重写） ---")
    response3: str = rag.chat("它和 LangChain 有什么关系？")
    print(f"助手: {response3}")

    # ---- 打印会话历史 ----
    print("\n--- 会话历史 ---")
    history = rag.get_history("default")
    for i, msg in enumerate(history, 1):
        role_label: str = "用户" if msg["role"] == "user" else "助手"
        print(f"{i}. [{role_label}] {msg['content'][:80]}...")  # 截取前 80 字符

    print("\n自测完成!")
