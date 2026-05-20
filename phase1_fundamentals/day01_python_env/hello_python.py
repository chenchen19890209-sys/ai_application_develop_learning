"""
hello_python.py
Python环境检查工具 — 验证开发环境是否配置正确

功能：
1. 检查Python版本是否符合要求（3.11+）
2. 检查是否在虚拟环境中运行
3. 加载.env文件并读取配置
4. 验证必要的环境变量是否已设置

学习目标：
1. 理解sys模块的基本用法
2. 学会使用os.getenv()读取环境变量
3. 掌握python-dotenv加载.env文件
4. 了解条件判断的基本语法
"""
import sys  # 系统相关功能，如获取Python版本
import os   # 操作系统相关功能，如读取环境变量
from pathlib import Path  # 路径处理，比字符串拼接更安全


def check_python_version():
    """检查Python版本是否为3.11或更高版本"""
    # sys.version_info 返回版本信息元组，如 (3, 11, 5, 'final', 0)
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")

    # 要求Python 3.11及以上（本课程基于3.11特性）
    if version.major == 3 and version.minor >= 11:
        print("✅ Python版本符合要求（3.11+）")
        return True
    else:
        print(f"⚠️ 建议使用Python 3.11+，当前版本: {version.major}.{version.minor}")
        return False


def check_virtualenv():
    """检查是否在虚拟环境中运行"""
    # sys.prefix: 当前Python环境的安装路径
    # sys.base_prefix: 系统原始Python的安装路径
    # 如果两者不同，说明在虚拟环境中
    in_venv = sys.prefix != sys.base_prefix

    if in_venv:
        print(f"✅ 已在虚拟环境中")
        print(f"   虚拟环境路径: {sys.prefix}")
        return True
    else:
        print("⚠️ 未使用虚拟环境（建议使用 python -m venv venv 创建）")
        return False


def check_env_file():
    """检查.env文件是否存在并加载配置"""
    # 项目根目录路径（day01_python_env -> phase1_fundamentals -> 项目根目录）
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"

    if not env_file.exists():
        print(f"⚠️ 未找到 .env 文件（路径: {env_file}）")
        print(f"   请复制 .env.example 为 .env 并填入你的 API Key")
        return False

    # 使用 python-dotenv 加载 .env 文件
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)  # 将.env中的配置加载到环境变量
        print(f"✅ .env 文件加载成功（路径: {env_file}）")
        return True
    except ImportError:
        print("❌ 请先安装 python-dotenv: pip install python-dotenv")
        return False


def check_env_variables():
    """检查必要的环境变量是否已设置"""
    # 检查LLM API Key（最重要的配置项）
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "your_api_key_here":
        print(f"✅ OPENAI_API_KEY: 已设置（{api_key[:8]}...{api_key[-4:]}）")
    elif api_key == "your_api_key_here":
        print("⚠️ OPENAI_API_KEY 为占位值，请修改 .env 文件填入真实 API Key")
    else:
        print("❌ OPENAI_API_KEY 未设置！请在 .env 文件中配置")

    # 检查其他常用配置项（带默认值，未设置也不报错）
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    print(f"   OPENAI_BASE_URL: {base_url}")

    model = os.getenv("OPENAI_MODEL", "deepseek-v4-flash")
    print(f"   OPENAI_MODEL: {model}")

    temperature = os.getenv("TEMPERATURE", "0.7")
    print(f"   TEMPERATURE: {temperature}")


def main():
    """主函数 — 运行所有环境检查"""
    print("=" * 60)
    print("Python 环境检查工具 — AI大模型应用开发")
    print("=" * 60)

    # 存储各项检查结果
    results = {}

    # 第1步：检查Python版本
    print("\n📋 1. Python版本检查:")
    print("-" * 40)
    results["python"] = check_python_version()

    # 第2步：检查虚拟环境
    print("\n📋 2. 虚拟环境检查:")
    print("-" * 40)
    results["venv"] = check_virtualenv()

    # 第3步：检查.env文件
    print("\n📋 3. 环境变量文件检查:")
    print("-" * 40)
    results["env_file"] = check_env_file()

    # 第4步：检查配置变量
    print("\n📋 4. 环境变量配置检查:")
    print("-" * 40)
    check_env_variables()

    # 打印汇总结果
    print("\n" + "=" * 60)
    print("检查汇总:")
    print("-" * 40)
    all_pass = True  # 标记是否全部通过
    for name, result in results.items():
        status = "✅ 通过" if result else "⚠️ 需处理"
        if not result:
            all_pass = False
        print(f"  {name}: {status}")

    print("-" * 40)
    if all_pass:
        print("🎉 所有检查通过！环境配置正确，可以开始学习！")
    else:
        print("💡 部分检查未通过，请按提示处理后再开始学习")
    print("=" * 60)


# 程序入口 — 当直接运行此文件时执行main()
if __name__ == "__main__":
    main()