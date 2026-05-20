"""
课程公共配置文件 — 所有天的代码都可以直接导入复用
使用原生 openai SDK，不依赖 LangChain

用法:
    from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
"""
import os
from dotenv import load_dotenv

# 加载项目根目录下的 .env 文件
load_dotenv()

# ==================== LLM API 配置（OpenAI 兼容标准）====================
# API密钥，用于身份验证
# ⚠️ 安全提示：必须通过环境变量设置，不允许硬编码
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "未设置 OPENAI_API_KEY 环境变量！\n"
        "请按照以下步骤配置：\n"
        "1. 复制 .env.example 为 .env\n"
        "2. 在 .env 文件中填入你的 API Key\n"
        "3. 根据使用的平台设置 OPENAI_BASE_URL 和 OPENAI_MODEL\n"
    )

# API的基础请求地址（OpenAI兼容接口）
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")

# 默认使用的大模型名称
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "deepseek-v4-flash")

# ==================== 向后兼容别名 ====================
DEEPSEEK_API_KEY = OPENAI_API_KEY
DEEPSEEK_BASE_URL = OPENAI_BASE_URL
LLM_MODEL = OPENAI_MODEL

# ==================== LLM 通用参数 ====================
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# ==================== 向量模型配置（RAG阶段使用）====================
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")

# ==================== HuggingFace 配置 ====================
HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")

# ==================== 其他配置 ====================
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")