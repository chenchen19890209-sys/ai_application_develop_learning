# Day 01: Python环境配置与开发工具

> 🎯 **学习目标**
>
> - 完成Python 3.11安装与验证
> - 理解虚拟环境的概念并创建第一个venv
> - 掌握pip包管理器的常用命令
> - 学会使用requirements.txt管理项目依赖
> - 理解环境变量的作用并用python-dotenv读取配置

---

## 📖 课程介绍

欢迎来到 **AI大模型应用开发教程**！

### 本课程特点

- 🎯 **从零开始**：无需编程基础，循序渐进学习
- 💻 **实战导向**：边学边做，每个知识点都有代码示例
- 🚀 **Agent优先**：先理解Agent核心范式，RAG作为工具融入
- 🛠️ **协议而非框架**：使用原生openai SDK + MCP协议，不绑定特定框架
- ⚡ **精简高效**：24天掌握Python → LLM → Agent → RAG → 实战全链路

### 今天我们将学习

1. ✅ Python 3.11的安装和验证
2. ✅ 虚拟环境的概念和使用
3. ✅ pip包管理器的常用命令
4. ✅ requirements.txt的作用
5. ✅ 环境变量的设置和读取
6. ✅ 实战：编写第一个Python程序

**准备好了吗？让我们开始Python之旅吧！** 🚀

---

## 📚 新知识讲解

### 1. Python 3.11安装

**比喻**：就像建房子需要打地基，Python版本就是我们的"地基"。3.11性能比3.10快10-60%，稳定性好，兼容性强。

**验证安装：**
```bash
python --version
# 应该显示：Python 3.11.x
```

---

### 2. 虚拟环境（Virtual Environment）

**比喻**：虚拟环境就像每个项目的"小房间"。没有虚拟环境，所有项目共用一个"大客厅"容易混乱。

```bash
# 进入项目目录
cd ai_develop_learning_claude

# 创建虚拟环境
python -m venv venv

# 激活（Windows）
venv\Scripts\activate

# 退出
deactivate
```

---

### 3. pip包管理器

**比喻**：pip就像"应用商店"，可以下载各种Python库。

```bash
pip install requests              # 安装库
pip install requests==2.31.0      # 安装指定版本
pip list                          # 查看已安装的库
pip freeze > requirements.txt     # 导出依赖列表
pip install -r requirements.txt   # 从文件安装依赖
# 国内镜像加速
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

---

### 4. requirements.txt文件

记录项目所需的所有库及其版本，方便他人复现环境。

```txt
requests==2.31.0
numpy==1.24.3
pandas==2.0.3
```

---

### 5. 环境变量配置

**比喻**：环境变量就像"全局便签"，所有程序都能看到。用于存储API密钥、配置不同环境。

**Python中读取环境变量：**
```python
import os
from dotenv import load_dotenv

load_dotenv()  # 从.env文件加载配置

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
```

---

## 💡 实例演示

### 实例1：Python环境检查工具

完整代码见 [hello_python.py](hello_python.py)，演示检查Python版本、虚拟环境状态、.env文件加载。

**运行方法：**
```bash
python hello_python.py
```

**预期输出：**
```
==================================================
Python 环境检查工具
==================================================
Python版本: 3.11.x
✅ 已在虚拟环境中
✅ .env 文件加载成功
OPENAI_API_KEY: 已设置
OPENAI_MODEL: deepseek-v4-flash
==================================================
环境配置检查完成！
==================================================
```

---

## ✍️ 练习题

### 练习1：基础题

1. 在你的电脑上安装Python 3.11，并验证版本号
2. 创建一个名为 `test_env` 的虚拟环境，激活它，然后退出
3. 使用pip安装 `requests` 库，然后查看已安装的包列表

### 练习2：进阶题

1. 创建项目文件夹，在其中：创建虚拟环境 → 安装 `numpy` 和 `pandas` → 生成 `requirements.txt`
2. 设置一个环境变量 `MY_NAME`，值为你的名字，然后在Python中读取并打印
3. 复制 `.env.example` 为 `.env`，填入真实的 API Key，运行 `hello_python.py` 验证

### 练习3：挑战题

创建一个自动化环境配置脚本 `setup_env.py`：
- 自动检测Python版本
- 如果没有虚拟环境，自动创建
- 自动安装 `requirements.txt` 中的依赖
- 检查 `.env` 文件是否存在，不存在则提示用户创建

---

## 🔮 后一天知识展望

明天我们将学习 **Python控制流程**：if-elif-else 条件判断、for/while 循环、match/case 模式匹配（Python 3.11新特性）。

**预习建议：** 思考什么是"条件判断"（如果...那么...），想想生活中的循环例子。

---

## 📝 今日总结

今天我们学习了：
- ✅ Python 3.11的安装和验证
- ✅ 虚拟环境的概念和使用
- ✅ pip包管理器的常用命令
- ✅ 环境变量的设置和读取

**关键要点：**
1. 始终使用虚拟环境隔离项目
2. 用 `requirements.txt` 管理依赖
3. **不要硬编码敏感信息**（用环境变量 + `.env` 文件）

---

## 🚀 下一步

1. 完成所有练习题
2. 确保Python环境配置正确
3. 准备好学习明天的控制流程

**加油！你的Python之旅开始了！** 💪

---

## 📖 参考资料

- [Python官方文档](https://docs.python.org/3/)
- [pip官方文档](https://pip.pypa.io/)
- [python-dotenv文档](https://pypi.org/project/python-dotenv/)