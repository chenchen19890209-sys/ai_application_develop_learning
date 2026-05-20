"""
example.py — Day 23 完整演示：Web UI 与部署

演示内容：
1. 环境配置 — 生成 .env 模板
2. 生产就绪检查 — 检查部署前置条件
3. AgentService 后端 — 会话管理和查询
4. 部署配置 — Docker Compose / Nginx 配置生成
5. 部署指南 — 完整的部署步骤
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent_service import AgentService
from deployment import DeploymentConfig


def demo_env_template():
    """演示 1：生成环境配置模板"""
    print("\n" + "=" * 60)
    print("  演示 1：环境配置 — 生成 .env 模板")
    print("=" * 60)

    template = DeploymentConfig.generate_env_template()
    # 只显示关键配置项（不显示完整模板以避免泄露）
    lines = template.strip().split("\n")
    print("\n  📋 关键配置项：")
    for line in lines:
        line = line.strip()
        if line and not line.startswith("# ="):
            if line.startswith("#"):
                continue
            key = line.split("=")[0] if "=" in line else ""
            print(f"    {key}")


def demo_production_check():
    """演示 2：生产就绪检查"""
    print("\n" + "=" * 60)
    print("  演示 2：生产环境就绪检查")
    print("=" * 60)

    checks = DeploymentConfig.check_production_readiness()
    print("\n  📋 检查结果：")
    for check, passed in checks.items():
        status = "✅ 通过" if passed else "❌ 未通过"
        print(f"    {status} — {check}")

    all_passed = all(checks.values())
    if all_passed:
        print("\n  ✅ 所有检查通过，可以部署！")
    else:
        print(f"\n  ⚠️ {sum(1 for v in checks.values() if not v)} 项未通过，请检查配置。")


def demo_agent_service():
    """演示 3：AgentService 后端服务"""
    print("\n" + "=" * 60)
    print("  演示 3：AgentService — 会话管理和查询")
    print("=" * 60)

    service = AgentService()

    # 创建会话
    session_id = service.create_session()
    print(f"\n  🆕 创建会话: {session_id}")

    # 健康检查
    health = service.health_check()
    print(f"  🏥 健康检查: {health['status']}")
    print(f"     活跃会话: {health['active_sessions']}")

    # 模拟对话
    try:
        response = service.query(session_id, "什么是 RAG？它有什么优势？")
        print(f"\n  👤 用户: 什么是 RAG？它有什么优势？")
        print(f"  🤖 Agent: {response.answer[:150]}...")
        print(f"     步数: {response.total_steps}, 耗时: {response.total_time_ms:.0f}ms")

        # 多轮对话
        response = service.query(session_id, "它和传统搜索有什么区别？")
        print(f"\n  👤 用户: 它和传统搜索有什么区别？")
        print(f"  🤖 Agent: {response.answer[:150]}...")
        print(f"     步数: {response.total_steps}, 耗时: {response.total_time_ms:.0f}ms")

        # 查看会话信息
        info = service.get_session_info(session_id)
        if info:
            print(f"\n  📊 会话统计: {info['query_count']} 轮对话")
            print(f"     Agent 统计: {info['agent_stats']}")

    except Exception as e:
        print(f"  ⚠️ LLM 调用失败: {e}")


def demo_deployment_config():
    """演示 4：部署配置生成"""
    print("\n" + "=" * 60)
    print("  演示 4：部署配置 — Docker & Nginx")
    print("=" * 60)

    # Docker Compose
    docker_compose = DeploymentConfig.generate_docker_compose()
    print("\n  🐳 Docker Compose 配置：")
    for line in docker_compose.strip().split("\n")[:10]:
        print(f"    {line}")
    print("    ...")

    # Nginx 配置
    nginx = DeploymentConfig.generate_nginx_config("rag-agent.example.com")
    print("\n  🌐 Nginx 配置（关键部分）：")
    for line in nginx.strip().split("\n")[:8]:
        print(f"    {line}")
    print("    ...")


def demo_deployment_guide():
    """演示 5：部署指南"""
    print("\n" + "=" * 60)
    print("  演示 5：部署指南")
    print("=" * 60)

    DeploymentConfig.print_deployment_guide()


def main():
    """主函数 — 运行所有演示"""
    print("=" * 60)
    print("  Day 23: Web UI 与部署")
    print("  Streamlit UI | AgentService | Docker | Nginx")
    print("=" * 60)

    try:
        demo_env_template()
        demo_production_check()
        demo_deployment_config()
        demo_deployment_guide()
        demo_agent_service()

        print("\n" + "=" * 60)
        print("  ✅ Day 23 所有演示完成！")
        print("=" * 60)
        print("\n  💡 Day 23 关键要点：")
        print("    1. AgentService — 会话管理 + 健康检查")
        print("    2. Streamlit Web UI — 聊天界面 + 来源展示")
        print("    3. Docker 部署 — 一键容器化")
        print("    4. Nginx 反向代理 — HTTPS + WebSocket")
        print("    5. 生产检查清单 — 环境变量/DEBUG/日志")
        print("\n  🚀 启动 Web UI：")
        print("    streamlit run phase5_capstone/day23_web_ui_deployment/web_ui.py")

    except Exception as e:
        print(f"\n  ❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
