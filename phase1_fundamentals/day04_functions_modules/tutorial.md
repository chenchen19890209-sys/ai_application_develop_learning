# Day 04: 函数、模块与高级特性

> 🎯 **学习目标**
>
> - 掌握函数的定义、参数传递（*args/**kwargs）和返回值
> - 理解lambda匿名函数和函数式编程
> - 学会使用类型提示（Type Hints）提高代码可读性
> - 掌握装饰器（Decorator）和生成器（Generator）的原理
> - 理解模块的导入机制和 `__name__ == "__main__"` 的作用

---

## 📖 前一天知识回顾

昨天我们学习了Python数据结构：
- ✅ 列表（有序可变）、字典（键值对）、元组（不可变）、集合（去重）
- ✅ 列表推导式 `[x for x in range(10) if x % 2 == 0]`
- ✅ 字典推导式 `{k: v for k, v in items}`

**关键复习：**
```python
# 数据结构选择速记
# 有序可变 → list   |   键查找 → dict
# 去重/集合运算 → set   |   不可变 → tuple
scores = [85, 90, 78]
avg = sum(scores) / len(scores)
```

---

## 📚 新知识讲解

### 1. 函数定义与参数

**比喻**：函数就像一个"菜谱"——给定输入（食材），按步骤操作，得到输出（菜品）。

```python
# 基本定义
def greet(name):
    """向指定的人打招呼"""  # 文档字符串（docstring）
    return f"你好，{name}！"

# 默认参数 — 调用时可省略
def greet(name, greeting="你好"):
    return f"{greeting}，{name}！"

# *args — 接收任意数量的位置参数（打包成元组）
def sum_all(*args):
    return sum(args)

# **kwargs — 接收任意数量的关键字参数（打包成字典）
def print_info(**kwargs):
    for key, value in kwargs.items():
        print(f"{key}: {value}")
```

---

### 2. lambda匿名函数

**比喻**：lambda就像"便利贴"——用完即扔的小函数，不需要正式命名。

```python
# 传统def（3行）
def add(x, y):
    return x + y

# lambda一行搞定
add = lambda x, y: x + y

# 常用于sorted/map/filter的参数
students = [{"name": "张三", "score": 85}, {"name": "李四", "score": 92}]
students.sort(key=lambda s: s["score"])  # 按成绩排序
```

---

### 3. 类型提示（Type Hints）

Python 3.5+支持，不影响运行时行为，但极大提高代码可读性和IDE支持：

```python
from typing import List, Dict, Optional, Callable

def calculate_average(scores: List[float]) -> float:
    """计算平均分"""
    return sum(scores) / len(scores)

def find_student(name: str) -> Optional[Dict]:
    """查找学生，找不到返回None"""
    ...

# 在AI开发中尤为重要 — LLM函数调用的JSON Schema就是从Type Hints生成的！
```

---

### 4. 装饰器（Decorator）

**比喻**：装饰器就像"包装纸"——在不修改原函数的情况下，给它添加额外的功能。

```python
import time

def timer(func):
    """测量函数执行时间的装饰器"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} 耗时: {elapsed:.3f}秒")
        return result
    return wrapper

@timer  # 使用装饰器
def slow_function():
    time.sleep(1.5)

slow_function()  # 输出: slow_function 耗时: 1.500秒
```

---

### 5. 生成器（Generator）

**比喻**：生成器像"水龙头"——需要时才产生数据，而不是一次性把所有数据装入内存。

```python
# 传统方式：一次性生成所有数据（占内存）
def get_squares_list(n):
    return [x ** 2 for x in range(n)]

# 生成器：用yield按需生成（省内存）
def get_squares_gen(n):
    for x in range(n):
        yield x ** 2

# 生成器表达式 — 用()代替[]
squares = (x ** 2 for x in range(1_000_000))  # 不占内存！
```

---

### 6. 模块导入机制

```python
# 导入整个模块
import math
math.sqrt(16)

# 导入特定函数
from math import sqrt, pow

# 只导入为别名
import numpy as np

# __name__ == "__main__" 的作用：
# 当直接运行该文件时，__name__ 为 "__main__"
# 当被其他文件import时，__name__ 为模块名
if __name__ == "__main__":
    main()
```

---

## 💡 实例演示

### 实例1：装饰器实战（计时器、缓存、重试）

完整代码见 [functions_demo.py](functions_demo.py) 的装饰器部分。

### 实例2：生成器实战（大文件逐行处理）

完整代码见 [functions_demo.py](functions_demo.py) 的生成器部分。

**运行方法：**
```bash
python functions_demo.py
```

---

## ✍️ 练习题

### 练习1：基础题

1. 编写函数 `calculate(operation, a, b)`，根据 operation 执行加减乘除
2. 用lambda写一个排序key：按字符串长度排序 `["a", "abc", "ab"]`
3. 给第1题的函数添加类型提示

### 练习2：进阶题

1. 写一个装饰器 `@retry(n)`，让函数在失败时自动重试n次
2. 写一个生成器 `token_batch(text, batch_size)`，每次yield指定数量的token
3. 写一个带缓存的函数（用字典手动实现memoization）

### 练习3：挑战题

实现一个简单的API请求重试装饰器：
- 支持指数退避（1s → 2s → 4s → 8s）
- 支持白名单（只重试特定异常）
- 记录每次重试的日志

---

## 🔮 后一天知识展望

明天是Python基础的最后一天，我们将学习 **文件IO、异常处理、正则表达式**，以及NumPy和Pandas入门，为后续AI数据处理打下基础。

---

## 📝 今日总结

今天我们学习了：
- ✅ 函数的定义、参数传递（*args/**kwargs）
- ✅ lambda匿名函数
- ✅ 类型提示（Type Hints）
- ✅ 装饰器的原理和使用
- ✅ 生成器的内存优势
- ✅ 模块导入机制

**关键要点：**
1. `*args` 打包位置参数为元组，`**kwargs` 打包关键字参数为字典
2. **装饰器 = 高阶函数**，在不修改原函数的情况下添加功能
3. **生成器 = 懒加载**，用 `yield` 按需生成，大量数据时省内存
4. Type Hints 在AI开发中用于生成LLM工具调用的JSON Schema

---

## 🚀 下一步

1. 完成所有练习题
2. 重点理解装饰器和生成器（AI开发中常用）
3. 准备好明天的文件处理和数据科学基础

**加油！你的Python武器库越来越丰富了！** 💪

---

## 📖 参考资料

- [Python函数文档](https://docs.python.org/3/tutorial/controlflow.html#defining-functions)
- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/)
- [Python装饰器详解](https://docs.python.org/3/glossary.html#term-decorator)
- [PEP 255 — 生成器](https://peps.python.org/pep-0255/)