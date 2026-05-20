# Day 05: 文件处理与数据处理

> 🎯 **学习目标**
>
> - 掌握Python文件读写（文本/CSV/JSON）和with语句
> - 理解异常处理（try/except/finally）和自定义异常
> - 学会使用正则表达式进行文本匹配和替换
> - 掌握NumPy数组操作和Pandas数据分析基础
> - 实战：CSV数据读取→清洗→分析→保存的完整流程

---

## 📖 前一天知识回顾

昨天我们学习了Python函数和高级特性：
- ✅ 函数定义、*args/**kwargs、lambda匿名函数
- ✅ 类型提示（Type Hints）和装饰器（Decorator）
- ✅ 生成器（Generator）的惰性求值
- ✅ 模块导入和 `__name__ == "__main__"`

**关键复习：**
```python
# 装饰器 = 包装函数，不修改原函数添加功能
@timer
def slow_func():
    time.sleep(1)

# 生成器 = 用yield按需产生数据，省内存
def gen():
    for i in range(10):
        yield i
```

**今天**是Python基础的最后一天，将文件处理、异常、正则、NumPy和Pandas合并学习。

---

## 📚 新知识讲解

### 第一部分：文件、异常与正则

### 1. 文件读写

**比喻**：文件操作就像图书馆借书——先打开（open），做笔记（read/write），最后归还（close）。`with`语句就是"自动归还"。

```python
# 文本文件读取
with open("data.txt", "r", encoding="utf-8") as f:
    content = f.read()  # 读取全部

# 逐行读取（大文件推荐）
with open("data.txt", "r", encoding="utf-8") as f:
    for line in f:
        print(line.strip())

# 写入文件
with open("output.txt", "w", encoding="utf-8") as f:
    f.write("Hello, World!\n")

# 文件模式: 'r'读, 'w'写(覆盖), 'a'追加, 'rb'二进制读
```

### 2. 异常处理

**比喻**：异常处理就像安全气囊——平时不显眼，出问题时保护程序不会崩溃。

```python
try:
    result = 10 / 0  # 可能出错的代码
except ZeroDivisionError as e:
    print(f"不能除以零: {e}")  # 出错时的处理
except Exception as e:
    print(f"其他错误: {e}")
else:
    print("没有异常时执行")  # 可选
finally:
    print("总是执行")  # 可选，用于清理资源
```

### 3. 正则表达式

**比喻**：正则表达式就像"模板匹配"——用来检查字符串是否符合某种模式。

```python
import re

text = "联系方式: zhangsan@mail.com, 13800001111"

# 搜索
email = re.search(r'\w+@\w+\.\w+', text)  # r前缀=原始字符串
print(email.group())  # zhangsan@mail.com

# 全部匹配
phones = re.findall(r'1\d{10}', text)  # \d=数字, {10}=重复10次
print(phones)  # ['13800001111']

# 替换
masked = re.sub(r'\d{8}(\d{3})', r'********\1', "13800001111")
print(masked)  # 138********111
```

---

### 第二部分：NumPy与Pandas入门

### 4. NumPy基础

NumPy是Python科学计算的基础库，核心是**ndarray**（N维数组）——比Python列表快10-100倍。

```python
import numpy as np

# 创建数组
arr = np.array([1, 2, 3, 4, 5])
zeros = np.zeros((3, 3))     # 3x3全0矩阵
ones = np.ones((2, 4))       # 2x4全1矩阵
rand = np.random.randn(100)   # 100个正态分布随机数

# 向量化运算（无需循环！）
arr = arr * 2            # 每个元素乘2
result = arr + arr       # 对应元素相加

# 切片
print(arr[1:4])          # 索引1-3的元素
print(arr[arr > 3])      # 布尔索引：所有大于3的元素
```

### 5. Pandas基础

Pandas是数据分析的核心工具，提供**DataFrame**（二维表格）和**Series**（一维序列）。

```python
import pandas as pd

# 读取数据
df = pd.read_csv("data.csv")
df = pd.read_json("data.json")

# 查看数据
df.head()      # 前5行
df.info()      # 列信息
df.describe()  # 统计摘要

# 数据操作
df["new_col"] = df["col1"] + df["col2"]  # 新增列
filtered = df[df["score"] > 80]          # 过滤
sorted_df = df.sort_values("score", ascending=False)  # 排序
grouped = df.groupby("category")["value"].mean()      # 分组聚合
```

---

## 💡 实例演示

### 实例1：安全的文件读写 + 异常处理

完整代码见 [file_exception_demo.py](file_exception_demo.py)，演示 `with` 语句、`try/except`、自定义异常、正则清洗数据。

### 实例2：NumPy + Pandas 数据分析流程

完整代码见 [data_processing_demo.py](data_processing_demo.py)，演示从CSV读取→NumPy数组计算→Pandas分析→保存结果。

**运行方法：**
```bash
python file_exception_demo.py
python data_processing_demo.py
```

---

## ✍️ 练习题

### 练习1：基础题

1. 将一段文本写入文件，再读出来打印
2. 写一个 `safe_divide(a, b)` 函数，用 try/except 处理除零错误
3. 用正则表达式匹配一个字符串中所有的中文字符
4. 创建一个3x3的NumPy数组，计算行和与列和

### 练习2：进阶题

1. 写一个CSV文件读取函数，自动检测编码（utf-8/gbk），读不到文件时给出友好提示
2. 用Pandas读取CSV → 过滤特定条件 → 用NumPy计算统计信息 → 保存结果
3. 写一个正则表达式，验证邮箱格式是否正确

### 练习3：挑战题

实现一个完整的数据清洗流程：
- 从CSV文件读取数据（可能有缺失值、异常值）
- 用正则清洗文本列（去除特殊字符、统一格式）
- 用Pandas填充缺失值、去除异常值
- 用NumPy计算统计摘要
- 将清洗后的数据和统计报告保存到文件

---

## 🔮 后一天知识展望

**Python基础阶段到此结束！** 明天我们将进入Phase 2：**LLM核心能力**——学习如何调用大语言模型API、使用原生openai SDK与LLM交互。

预习建议：注册DeepSeek API Key，确保 `.env` 文件配置正确。

---

## 📝 今日总结

今天我们学习了：
- ✅ 文件读写（open/with/read/write/append）
- ✅ 异常处理（try/except/else/finally）
- ✅ 正则表达式（search/findall/sub）
- ✅ NumPy数组操作（向量化、切片、布尔索引）
- ✅ Pandas数据分析（DataFrame/读取/过滤/分组/聚合）

**关键要点：**
1. **始终用 `with` 语句打开文件**（自动关闭，防止资源泄漏）
2. 捕获**具体异常**而不是裸Exception，方便定位问题
3. **r-string**（`r'\d+'`）写正则，避免转义问题
4. NumPy/Pandas用**向量化操作**而非循环，快10-100倍

---

## 🚀 下一步

1. 完成所有练习题
2. 确保 `.env` 文件中有有效的 `OPENAI_API_KEY`
3. 安装 `openai` 库：`pip install openai`

**Python阶段结束，AI之旅正式开始！准备好迎接LLM的力量！** 💪

---

## 📖 参考资料

- [Python文件IO文档](https://docs.python.org/3/tutorial/inputoutput.html)
- [re模块文档](https://docs.python.org/3/library/re.html)
- [NumPy快速入门](https://numpy.org/doc/stable/user/quickstart.html)
- [Pandas入门教程](https://pandas.pydata.org/docs/getting_started/)