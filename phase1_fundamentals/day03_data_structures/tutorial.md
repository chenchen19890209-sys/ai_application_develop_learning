# Day 03: Python数据结构与推导式

> 🎯 **学习目标**
>
> - 掌握列表(list)、字典(dict)、元组(tuple)、集合(set)的使用
> - 学会列表推导式和字典推导式，写出简洁高效的代码
> - 理解各数据结构的适用场景和性能特点
> - 实战：用数据结构重构学生成绩管理系统

---

## 📖 前一天知识回顾

昨天我们学习了Python控制流程：
- ✅ if-elif-else 条件判断和 match/case 模式匹配
- ✅ for循环和while循环的区别与适用场景
- ✅ break（跳出循环）、continue（跳过本次）、pass（占位符）
- ✅ 实战：猜数字游戏、成绩等级判定系统

**关键复习：**
```python
# 条件判断
if score >= 90:
    level = "优秀"

# for循环遍历
for i in range(5):
    print(i)

# while循环（注意退出条件！）
while count < 5:
    count += 1
```

---

## 📚 新知识讲解

### 1. 列表（List）— 有序的可变集合

**比喻**：列表就像一个购物清单，可以按顺序记录多个物品，随时增删改。

```python
# 创建列表
fruits = ["苹果", "香蕉", "橙子"]
numbers = [1, 2, 3, 4, 5]
mixed = [1, "hello", 3.14, True]  # 可包含不同类型

# 索引访问（从0开始，负数从末尾倒着数）
fruits[0]    # "苹果"（第一个）
fruits[-1]   # "橙子"（最后一个）

# 切片 [start:stop:step] — 不包含stop
fruits[1:3]  # ['香蕉', '橙子']
fruits[::-1] # ['橙子', '香蕉', '苹果']（反转列表）

# 修改
fruits.append("葡萄")       # 末尾添加
fruits.insert(1, "草莓")    # 指定位置插入
fruits.remove("香蕉")       # 按值删除
last = fruits.pop()         # 删除并返回最后一个

# 常用方法
numbers.sort()              # 原地排序
len(numbers)                # 列表长度
numbers.count(1)            # 统计某元素出现次数
sum(numbers) / max(numbers) / min(numbers)
```

---

### 2. 字典（Dictionary）— 键值对集合

**比喻**：字典就像真实的字典，通过"键"（单词）查找"值"（解释），查找速度极快（O(1)）。

```python
# 创建字典
student = {
    "name": "张三",
    "age": 20,
    "score": 85
}

# 访问
student["name"]            # "张三"（键不存在会报错）
student.get("phone", "N/A")  # 安全访问，键不存在返回默认值

# 修改
student["phone"] = "123"   # 添加/修改键值对
del student["phone"]        # 删除
value = student.pop("age")  # 删除并返回值

# 遍历
for key in student:                  # 遍历键
for key, value in student.items():  # 遍历键值对（最常用）
```

---

### 3. 元组（Tuple）— 不可变的列表

```python
point = (10, 20)
colors = ("red", "green", "blue")

# 元组不可修改（线程安全、可作为字典的键）
# point[0] = 15  # ❌ 报错！

# 元组解包（优雅的多变量赋值）
x, y = point  # x=10, y=20
```

**何时用元组？** 数据不应被修改时（坐标、RGB颜色）、函数返回多个值、作为字典的键。

---

### 4. 集合（Set）— 无序的不重复集合

```python
fruits = {"苹果", "香蕉", "橙子"}
numbers = set([1, 2, 3, 3, 4])  # 自动去重: {1, 2, 3, 4}

# 集合运算
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}
a & b   # 交集: {3, 4}
a | b   # 并集: {1, 2, 3, 4, 5, 6}
a - b   # 差集: {1, 2}
```

---

### 5. 列表推导式 — 简洁优雅的列表创建

**比喻**：传统方式像一个个手写，推导式像用模具批量生产。

```python
# 传统方式（4行）
squares = []
for x in range(10):
    squares.append(x ** 2)

# 列表推导式（1行）
squares = [x ** 2 for x in range(10)]

# 带条件的推导式
even_squares = [x ** 2 for x in range(10) if x % 2 == 0]

# 带if-else的推导式
labels = ["偶数" if x % 2 == 0 else "奇数" for x in range(5)]
```

### 6. 字典推导式

```python
# 创建平方数字典
squares_dict = {x: x**2 for x in range(5)}

# 过滤字典
scores = {"张三": 85, "李四": 92, "王五": 78}
excellent = {name: score for name, score in scores.items() if score >= 90}
```

---

## 💡 实例演示

### 实例1：数据结构操作大全

完整代码见 [data_structures.py](data_structures.py)，涵盖列表的增删改查排序、字典的键值操作、集合运算、元组解包等所有常用操作。

### 实例2：用数据结构管理系统数据

完整代码见 [data_structures.py](data_structures.py)，展示如何在真实场景中选择和组合使用不同数据结构。

**运行方法：**
```bash
python data_structures.py
```

---

## ✍️ 练习题

### 练习1：基础题

1. 创建一个包含5个水果的列表，完成：在第2个位置插入新水果 → 删除最后的水果 → 排序
2. 创建一个字典存储个人信息（姓名、年龄、城市），添加"爱好"、修改年龄、遍历打印
3. 用列表推导式生成 1-100 之间所有能被3整除的数的平方

### 练习2：进阶题

1. 用字典推导式将一个字典的键值互换（{k: v} → {v: k}）
2. 有两个列表 `names = ["A", "B", "C"]` 和 `scores = [85, 92, 78]`，用 zip 和推导式创建一个字典
3. 用集合找出两个列表中共同的元素和不同的元素

### 练习3：挑战题

实现一个简单的通讯录系统：
- 用字典存储联系人（姓名 → 电话号码）
- 支持添加、删除、查询、模糊搜索
- 将所有联系人按姓名排序后显示

---

## 🔮 后一天知识展望

明天我们将学习 **函数、模块与高级特性**：函数定义和参数传递、lambda匿名函数、类型提示(Type Hints)、装饰器和生成器。

**预习建议：** 思考为什么要使用函数（代码复用），什么是"模块化编程"。

---

## 📝 今日总结

今天我们学习了：
- ✅ 列表的增删改查和切片（有序、可变）
- ✅ 字典的键值对操作（快速查找）
- ✅ 元组的不可变性（线程安全）
- ✅ 集合的去重和运算（交集/并集/差集）
- ✅ 列表推导式和字典推导式（简洁高效）

**关键要点：**
1. **列表有序可变** > **元组不可变**（线程安全）
2. **字典通过键查找值，O(1)速度极快**
3. **集合自动去重**，适合去重和集合运算
4. **推导式 = 简洁的循环**，Agency开发中大量使用

---

## 🚀 下一步

1. 完成所有练习题
2. 理解每种数据结构的最佳使用场景
3. 准备好学习明天的函数和模块

**加油！数据结构是编程的基石！** 💪

---

## 📖 参考资料

- [Python数据结构文档](https://docs.python.org/3/tutorial/datastructures.html)
- [Python推导式指南](https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions)