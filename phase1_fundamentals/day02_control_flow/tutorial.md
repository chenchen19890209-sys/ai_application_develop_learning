# Day 02: Python控制流程

> 🎯 **学习目标**
>
> - 掌握if-elif-else条件判断
> - 熟练使用for循环和while循环
> - 理解break/continue/pass控制语句
> - 学会match/case模式匹配（Python 3.11新特性）
> - 实战：猜数字游戏、成绩等级判定系统

---

## 📖 前一天知识回顾

昨天我们学习了Python环境配置：
- ✅ Python 3.11的安装和虚拟环境的创建
- ✅ pip包管理器和requirements.txt的使用
- ✅ 用 `python-dotenv` 加载 `.env` 文件
- ✅ 通过 `os.getenv()` 读取环境变量

**关键复习：**
```python
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
```

---

## 📚 新知识讲解

### 1. 条件判断（if-elif-else）

**比喻**：就像生活中的决策——如果下雨就带伞，如果阴天就带外套，否则什么都不带。

#### 基本语法

```python
# 简单if
age = 18
if age >= 18:
    print("你已成年")

# if-else
score = 75
if score >= 60:
    print("及格")
else:
    print("不及格")

# if-elif-else（多条件）
score = 85
if score >= 90:
    print("优秀")
elif score >= 80:
    print("良好")
elif score >= 70:
    print("中等")
elif score >= 60:
    print("及格")
else:
    print("不及格")
```

#### 比较运算符与逻辑运算符

| 运算符 | 含义 | 运算符 | 含义 |
|--------|------|--------|------|
| `==` | 等于 | `!=` | 不等于 |
| `>` | 大于 | `<` | 小于 |
| `>=` | 大于等于 | `<=` | 小于等于 |
| `and` | 并且 | `or` | 或者 |
| `not` | 取反 | `in` | 包含于 |

---

### 2. for循环

**比喻**：就像重复做同样的事情——跑10圈操场、给10个学生打分、检查100个文件。

```python
# range(start, stop, step)
for i in range(5):          # 0, 1, 2, 3, 4
    print(i)

for i in range(1, 10, 2):  # 1, 3, 5, 7, 9
    print(i)

# 遍历列表（带索引用enumerate）
fruits = ["苹果", "香蕉", "橙子"]
for index, fruit in enumerate(fruits):
    print(f"{index}: {fruit}")
```

---

### 3. while循环

**比喻**：只要条件满足，就一直做——水没开就继续加热，游戏没结束就继续玩。

```python
count = 0
while count < 5:
    print(count)
    count += 1  # ⚠️ 一定要更新条件，否则会无限循环！

# 用户输入循环
while True:
    user_input = input("输入'quit'退出: ")
    if user_input == "quit":
        break  # 跳出循环
```

---

### 4. 控制语句（break / continue / pass）

```python
# break — 立即跳出循环
for i in range(10):
    if i % 2 == 0:
        print(f"找到第一个偶数: {i}")
        break

# continue — 跳过本次循环，继续下一次
for i in range(10):
    if i % 2 == 0:
        continue  # 跳过偶数
    print(i)      # 只打印奇数

# pass — 占位符，什么都不做
def not_implemented_yet():
    pass
```

---

### 5. match/case 模式匹配（Python 3.11 新特性）

比传统的 if-elif-else 更清晰，尤其在处理多种取值情况时：

```python
# 传统写法
def get_status_text(code):
    if code == 200:
        return "成功"
    elif code == 404:
        return "未找到"
    elif code == 500:
        return "服务器错误"
    else:
        return "未知状态"

# match/case写法（Python 3.11+）
def get_status_text(code):
    match code:
        case 200:
            return "成功"
        case 404:
            return "未找到"
        case 500:
            return "服务器错误"
        case _:  # _ 是通配符，匹配所有未列出的情况
            return "未知状态"
```

---

## 💡 实例演示

### 实例1：猜数字游戏

完整代码见 [control_flow.py](control_flow.py)，综合运用 `while True`、`if-elif-else`、`break/continue`、`try-except` 和 `random` 模块。

### 实例2：成绩等级判定系统

完整代码见 [control_flow.py](control_flow.py) 的后半部分，展示函数定义、列表遍历、格式化输出等综合应用。

**运行方法：**
```bash
python control_flow.py
```

---

## ✍️ 练习题

### 练习1：基础题

1. 编写程序判断一个数是正数、负数还是零
2. 使用for循环打印1-100之间所有能被3整除的数
3. 使用while循环计算 1+2+3+...+100 的和

### 练习2：进阶题

1. 编写程序打印九九乘法表（嵌套循环）
2. 让用户输入5个数字，找出最大值和最小值（不用max/min函数）
3. 用 `match/case` 实现一个简单的四则运算选择器

### 练习3：挑战题

实现一个计算器：
- 支持加减乘除四种运算
- 用户可以连续计算
- 输入'quit'退出
- 处理除零错误
- 记录计算历史

---

## 🔮 后一天知识展望

明天我们将学习 **Python数据结构**：列表(list)、字典(dict)、元组(tuple)、集合(set)，以及强大的列表推导式和字典推导式。

**预习建议：** 思考什么是"列表"（购物清单），什么是"字典"（查单词）。

---

## 📝 今日总结

今天我们学习了：
- ✅ if-elif-else条件判断
- ✅ for循环和while循环
- ✅ break/continue/pass控制语句
- ✅ match/case模式匹配
- ✅ 实战：猜数字游戏、成绩等级系统

**关键要点：**
1. 条件判断让程序能做决策
2. 循环让程序能重复执行
3. **break 跳出循环，continue 跳过本次**
4. **while 循环一定要有退出条件，避免死循环**
5. match/case 让多条件分支代码更清晰

---

## 🚀 下一步

1. 完成所有练习题
2. 熟练掌握条件判断和循环
3. 准备好学习明天的数据结构

**加油！你的编程逻辑思维正在建立！** 💪

---

## 📖 参考资料

- [Python控制流文档](https://docs.python.org/3/tutorial/controlflow.html)
- [PEP 636 — match/case模式匹配](https://peps.python.org/pep-0636/)