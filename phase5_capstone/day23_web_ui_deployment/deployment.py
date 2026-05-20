"""
deployment.py — Day 23 部署配置模块

提供多种部署方案和配置工具：
1. 环境变量模板生成
2. Docker Compose 配置生成
3. 生产环境配置检查清单

设计原则：部署配置与业务代码分离，通过环境变量注入。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import json
from typing import Dict, List


class DeploymentConfig:
    """部署配置管理器 — 生成和管理部署相关配置"""

    @staticmethod
    def generate_env_template() -> str:
        """生成 .env 配置模板

        Returns:
            完整的 .env 模板内容
        """
        return """# ==================== LLM API 配置 ====================
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-v4-flash

# ==================== 向量模型配置 ====================
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
EMBEDDING_DEVICE=cpu
HF_ENDPOINT=https://hf-mirror.com

# ==================== LLM 参数 ====================
TEMPERATURE=0.3
MAX_TOKENS=2048
REQUEST_TIMEOUT=30
MAX_RETRIES=3

# ==================== 服务配置 ====================
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
MAX_SESSIONS=100
SESSION_TTL_SECONDS=3600

# ==================== 日志配置 ====================
LOG_LEVEL=INFO
DEBUG=false
"""

    @staticmethod
    def generate_docker_compose() -> str:
        """生成 Docker Compose 配置

        Returns:
            docker-compose.yml 内容
        """
        return """version: '3.8'

services:
  rag-agent-app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL}
      - OPENAI_MODEL=${OPENAI_MODEL}
      - EMBEDDING_MODEL=${EMBEDDING_MODEL}
      - HF_ENDPOINT=${HF_ENDPOINT}
    volumes:
      - ./data:/app/data          # 持久化索引数据
      - ./.env:/app/.env          # 环境变量
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
"""

    @staticmethod
    def generate_dockerfile() -> str:
        """生成 Dockerfile

        Returns:
            Dockerfile 内容
        """
        return """FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \\
    -i https://mirrors.aliyun.com/pypi/simple/

# 复制应用代码
COPY . .

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 启动命令
CMD ["streamlit", "run", "web_ui.py", \\
     "--server.address=0.0.0.0", \\
     "--server.port=8501", \\
     "--server.headless=true"]
"""

    @staticmethod
    def generate_nginx_config(domain: str = "example.com") -> str:
        """生成 Nginx 反向代理配置

        Args:
            domain: 域名

        Returns:
            Nginx 配置内容
        """
        return f"""server {{
    listen 80;
    server_name {domain};

    # 重定向 HTTP → HTTPS
    return 301 https://$host$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {domain};

    ssl_certificate     /etc/nginx/ssl/{domain}.pem;
    ssl_certificate_key /etc/nginx/ssl/{domain}.key;

    # Streamlit WebSocket 支持
    location / {{
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }}

    # 静态资源缓存
    location /static/ {{
        proxy_pass http://127.0.0.1:8501/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }}
}}
"""

    @staticmethod
    def check_production_readiness() -> Dict[str, bool]:
        """检查生产环境就绪状态

        检查清单：
        - 环境变量是否完整
        - API Key 是否已配置
        - 是否关闭了 DEBUG 模式
        - 日志级别是否合理

        Returns:
            检查结果字典，key=检查项，value=是否通过
        """
        checks = {}

        # 检查 API Key
        api_key = os.getenv("OPENAI_API_KEY", "")
        checks["API Key 已配置"] = bool(api_key) and "sk-your" not in api_key

        # 检查 DEBUG 模式
        debug = os.getenv("DEBUG", "false").lower()
        checks["DEBUG 已关闭"] = debug not in ("true", "1", "yes")

        # 检查日志级别
        log_level = os.getenv("LOG_LEVEL", "INFO")
        checks["日志级别合适"] = log_level in ("INFO", "WARNING", "ERROR")

        # 检查模型配置
        model = os.getenv("OPENAI_MODEL", "")
        checks["模型已配置"] = bool(model)

        return checks

    @staticmethod
    def print_deployment_guide():
        """打印部署指南"""
        print("""
╔══════════════════════════════════════════════════════════╗
║           RAG Agent 部署指南                              ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  📦 方案一：直接运行（开发/测试）                         ║
║  ─────────────────────────────                            ║
║  1. pip install -r requirements.txt                      ║
║  2. 配置 .env 文件                                       ║
║  3. streamlit run web_ui.py                              ║
║                                                          ║
║  🐳 方案二：Docker 部署（推荐生产）                       ║
║  ─────────────────────────────────                        ║
║  1. docker build -t rag-agent .                          ║
║  2. docker run -d -p 8501:8501 --env-file .env \\         ║
║       rag-agent                                          ║
║                                                          ║
║  ☸️  方案三：Docker Compose（多服务）                      ║
║  ───────────────────────────────────                      ║
║  1. docker-compose up -d                                 ║
║                                                          ║
║  🔒 生产环境检查清单：                                     ║
║  □ API Key 已配置（非默认值）                              ║
║  □ DEBUG=false                                           ║
║  □ LOG_LEVEL=INFO 或 WARNING                             ║
║  □ 配置了 HTTPS 反向代理（Nginx/Caddy）                   ║
║  □ 设置了资源限制（Docker memory/cpu limits）             ║
║  □ 配置了日志收集（ELK/Loki）                             ║
║  □ 配置了监控告警（Prometheus/Grafana）                   ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")
