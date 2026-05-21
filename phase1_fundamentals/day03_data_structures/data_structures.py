"""
data_structures.py
Python数据结构综合演示 — 列表、字典、元组、集合、推导式

功能：
1. 列表的增删改查、排序、切片、嵌套
2. 字典的键值操作、遍历、嵌套字典
3. 元组的不可变性、解包
4. 集合的去重、集合运算
5. 列表推导式和字典推导式
6. 实战：学生成绩管理系统v2.0（数据结构版）

学习目标：
1. 掌握四种数据结构的特性和适用场景
2. 学会用推导式写出简洁高效的代码
3. 能根据实际需求选择合适的数据结构
"""
import json  # JSON序列化，用于数据的保存和加载


# ==================== 第1部分：列表操作演示 ====================

def demo_list():
    """演示列表的各种操作"""
    print("=" * 50)
    print("📋 1. 列表（List）操作")
    print("-" * 50)

    # 创建列表 — 用[]包裹，元素用逗号分隔
    fruits = ["苹果", "香蕉", "橙子"]
    print(f"初始列表: {fruits}")

    # 索引访问 — 从0开始，负数从末尾倒数
    print(f"[0] 第一个: {fruits[0]}")    # 苹果
    print(f"[-1] 最后一个: {fruits[-1]}") # 橙子

    # 切片 [起始:结束:步长] — 不包含结束位置
    print(f"[1:3] 索引1-2: {fruits[1:3]}")     # ['香蕉', '橙子']
    print(f"[::-1] 反转: {fruits[::-1]}")       # ['橙子', '香蕉', '苹果']

    # 添加元素
    fruits.append("葡萄")       # 在末尾添加一个元素
    fruits.insert(1, "草莓")    # 在索引1位置插入
    fruits.extend(["柠檬", "桃子"])  # 扩展多个元素
    print(f"添加后: {fruits}")

    # 删除元素
    fruits.remove("香蕉")  # 按值删除（找不到会报错）
    del fruits[0]          # 按索引删除
    last = fruits.pop()    # 删除并返回最后一个元素
    print(f"删除后: {fruits}，pop出: {last}")

    # 排序 — sort()原地排序，sorted()返回新列表
    numbers = [3, 1, 4, 1, 5, 9, 2, 6]
    numbers.sort()               # 升序排序（原地修改）
    print(f"升序: {numbers}")
    numbers.sort(reverse=True)   # 降序排序
    print(f"降序: {numbers}")

    # 常用内置函数
    print(f"长度: {len(numbers)}")
    print(f"求和: {sum(numbers)}，最大值: {max(numbers)}，最小值: {min(numbers)}")
    print(f"1出现了{numbers.count(1)}次")

    # 列表嵌套 — 矩阵/二维数据
    matrix = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]
    print(f"矩阵: {matrix}")
    print(f"matrix[1][2] = {matrix[1][2]}")  # 第2行第3列=6


# ==================== 第2部分：字典操作演示 ====================

def demo_dict():
    """演示字典的各种操作"""
    print("\n" + "=" * 50)
    print("📋 2. 字典（Dictionary）操作")
    print("-" * 50)

    # 创建字典 — {键: 值} 格式
    student = {
        "name": "张三",
        "age": 20,
        "score": 85.5,
        "courses": ["Python", "AI", "Data"]
    }
    print(f"初始字典: {student}")

    # 访问 — 用[]或.get()
    print(f"姓名: {student['name']}")
    # .get(键, 默认值) — 键不存在时返回默认值，不会报错
    print(f"电话: {student.get('phone', '未提供')}")

    # 添加/修改 — 直接赋值
    student["phone"] = "138000000"  # 新键 → 添加
    student["age"] = 21             # 已有键 → 修改
    print(f"修改后: {student}")

    # 删除 — del 或 pop()
    del student["phone"]           # 直接删除
    age = student.pop("age")       # 删除并返回值
    print(f"pop出的age: {age}，删除后: {student}")

    # 遍历字典
    print("\n遍历方式:")
    print("键:", [k for k in student])        # 直接遍历=遍历键
    print("值:", [v for v in student.values()])
    # .items() — 最常用，同时获取键和值
    for key, value in student.items():
        print(f"  {key}: {value}")

    # 字典合并（Python 3.9+）
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 3, "c": 4}
    merged = d1 | d2  # | 运算符合并字典，后者覆盖前者
    print(f"合并: {merged}")  # {'a': 1, 'b': 3, 'c': 4}

    # 嵌套字典 — AI开发中常见（API响应、配置等）
    config = {
        "llm": {
            "model": "deepseek-v4-flash",
            "temperature": 0.7
        },
        "embedding": {
            "model": "BAAI/bge-small-zh-v1.5",
            "device": "cpu"
        }
    }
    print(f"LLM模型: {config['llm']['model']}")  # 嵌套访问


# ==================== 第3部分：元组和集合演示 ====================

def demo_tuple_and_set():
    """演示元组和集合的特性"""
    print("\n" + "=" * 50)
    print("📋 3. 元组（Tuple）与集合（Set）")
    print("-" * 50)

    # —— 元组 ——
    # 创建 — 用()或直接逗号分隔
    point = (10, 20)
    colors = "red", "green", "blue"  # 括号可省略
    single = (42,)  # 单元素元组需要加逗号！(42)是数字不是元组

    print(f"坐标: {point}")
    print(f"颜色: {colors}")

    # 元组不可修改
    try:
        point[0] = 15  # 这会报错！
    except TypeError as e:
        print(f"不可修改验证: {e}")

    # 元组解包 — 一行赋值多个变量
    x, y = point
    print(f"解包: x={x}, y={y}")

    # 多值交换（利用元组解包）
    a, b = 1, 2
    a, b = b, a  # 底层是元组打包→解包
    print(f"交换: a={a}, b={b}")

    # 函数多返回值（实际返回的是元组）
    def min_max_avg(numbers):
        """返回最小值、最大值、平均值"""
        return min(numbers), max(numbers), sum(numbers) / len(numbers)

    mn, mx, avg = min_max_avg([3, 1, 4, 1, 5])
    print(f"最小={mn}, 最大={mx}, 平均={avg:.2f}")

    # —— 集合 ——
    print()
    # 创建 — {}或set()，注意{}是空字典，空集合用set()
    fruits = {"苹果", "香蕉", "橙子"}
    numbers = set([1, 2, 3, 3, 4, 4, 5])  # 自动去重
    print(f"集合（自动去重）: {numbers}")

    # 增删元素
    fruits.add("葡萄")      # 添加
    fruits.discard("西瓜")  # 安全删除（不存在不报错）
    print(f"更新后: {fruits}")

    # 集合运算 — 交集/并集/差集
    set_a = {1, 2, 3, 4}
    set_b = {3, 4, 5, 6}
    print(f"A: {set_a}，B: {set_b}")
    print(f"  交集(A&B): {set_a & set_b}")   # 两边都有的
    print(f"  并集(A|B): {set_a | set_b}")   # 合并去重
    print(f"  差集(A-B): {set_a - set_b}")   # A中有B中没有的
    print(f"  对称差(A^B): {set_a ^ set_b}") # 只在一边出现的

    # 去重应用 — 列表去重最快的方式
    duplicates = [1, 2, 2, 3, 3, 3, 4]
    unique = list(set(duplicates))
    print(f"去重: {duplicates} → {unique}")

    # 成员检查 — set比list快得多（O(1) vs O(n)）
    print(f"'苹果'在集合中: {'苹果' in fruits}")  # check membership


# ==================== 第4部分：推导式演示 ====================

def demo_comprehensions():
    """演示列表推导式和字典推导式"""
    print("\n" + "=" * 50)
    print("📋 4. 推导式（Comprehensions）")
    print("-" * 50)

    # —— 列表推导式 ——
    # 基本格式: [表达式 for 变量 in 可迭代对象]

    # 生成平方数
    squares = [x ** 2 for x in range(10)]
    print(f"平方数: {squares}")

    # 带条件过滤: [表达式 for 变量 in 可迭代对象 if 条件]
    evens = [x for x in range(20) if x % 2 == 0]
    print(f"偶数: {evens}")

    # if-else在表达式中（注意位置！）
    labels = ["偶数" if x % 2 == 0 else "奇数" for x in range(5)]
    print(f"标签: {labels}")

    # 嵌套循环: [表达式 for x in xs for y in ys]
    pairs = [(x, y) for x in range(3) for y in range(3)]
    print(f"坐标对: {pairs}")

    # 字符串操作
    words = ["hello", "world", "python", "ai"]
    upper_words = [w.upper() for w in words]  # 转大写
    long_words = [w for w in words if len(w) > 3]  # 过滤短词
    print(f"大写: {upper_words}")
    print(f"长词(>3): {long_words}")

    # AI开发中常见的用法 — 处理API响应数据
    students = [
        {"name": "张三", "score": 85},
        {"name": "李四", "score": 92},
        {"name": "王五", "score": 78},
        {"name": "赵六", "score": 95}
    ]
    # 提取所有姓名
    names = [s["name"] for s in students]
    print(f"所有姓名: {names}")
    # 过滤优秀学生（score >= 90）
    excellent = [s["name"] for s in students if s["score"] >= 90]
    print(f"优秀学生: {excellent}")
    # 计算平均分
    avg_score = sum(s["score"] for s in students) / len(students)  # 生成器表达式
    print(f"平均分: {avg_score:.2f}")

    # —— 字典推导式 ——
    # 基本格式: {键表达式: 值表达式 for 变量 in 可迭代对象}

    # 数字→平方映射
    squares_dict = {x: x ** 2 for x in range(5)}
    print(f"\n字典推导式 — 平方映射: {squares_dict}")

    # 过滤字典
    scores = {"张三": 78, "李四": 92, "王五": 78, "赵六": 95}
    top_students = {k: v for k, v in scores.items() if v >= 90}
    print(f"优秀学生: {top_students}")

    # 字典翻转（键值互换）
    inverted = {v: k for k, v in scores.items()}
    print(f"翻转: {inverted}")

    # —— 集合推导式 ——
    # 基本格式: {表达式 for 变量 in 可迭代对象}
    unique_lengths = {len(word) for word in words}
    print(f"单词长度集合: {unique_lengths}")


# ==================== 第5部分：数据结构选择指南 ====================

def demo_selection_guide():
    """演示如何根据需求选择数据结构"""
    print("\n" + "=" * 50)
    print("📋 5. 数据结构选择指南")
    print("-" * 50)

    print("""
    选择决策树:
    ┌─ 需要键值对？ ──→ 是 → 用 dict（字典）
    │
    ├─ 需要去重 / 集合运算？ ──→ 是 → 用 set（集合）
    │
    ├─ 数据不可变？ ──→ 是 → 用 tuple（元组）
    │
    └─ 以上都不是 ──→ 用 list（列表）
    """)

    # 实际对比：用不同数据结构解决同一问题
    # 场景：存储一周的天气，每天一个温度值

    # list — 适合：有序数据、需要索引、需要排序
    temps_list = [22, 25, 23, 26, 24, 27, 25]
    print(f"列表版（可改、有序）: {temps_list}")
    print(f"  第三天: {temps_list[2]}°C")
    print(f"  最高温: {max(temps_list)}°C")

    # tuple — 适合：固定不变的数据
    temps_tuple = (22, 25, 23, 26, 24, 27, 25)
    print(f"元组版（不可改、有序）: {temps_tuple}")
    # temps_tuple[0] = 30  # ❌ 不能修改

    # dict — 适合：需要标签/键来查找
    temps_dict = {
        "周一": 22, "周二": 25, "周三": 23,
        "周四": 26, "周五": 24, "周六": 27, "周日": 25
    }
    print(f"字典版（键查找）: 周五={temps_dict['周五']}°C")

    # set — 适合：需要知道出现过哪些温度
    temps_set = {22, 25, 23, 26, 24, 27}
    print(f"集合版（去重）: 出现过的温度 {temps_set}")


# ==================== 第6部分：实战 — 学生成绩管理系统v2.0 ====================

def student_system_v2():
    """学生成绩管理系统 — 数据结构版"""
    print("\n" + "=" * 50)
    print("📊 6. 学生成绩管理系统 v2.0")
    print("-" * 50)

    # 用列表装所有学生，每个学生是一个字典
    students = []

    # 预设一些数据（省去手动输入）
    preset = [
        {"name": "张三", "scores": [85, 90, 78]},
        {"name": "李四", "scores": [92, 88, 95]},
        {"name": "王五", "scores": [78, 82, 80]},
        {"name": "赵六", "scores": [95, 93, 97]},
    ]
    for p in preset:
        students.append({
            "name": p["name"],
            "scores": p["scores"],
            "average": sum(p["scores"]) / len(p["scores"])  # 计算平均分
        })

    # 1. 显示所有学生信息
    print("\n所有学生:")
    for s in students:
        print(f"  {s['name']}: 成绩{s['scores']} 平均{s['average']:.1f}")

    # 2. 用推导式提取数据
    names = [s["name"] for s in students]  # 所有姓名
    averages = [s["average"] for s in students]  # 所有平均分
    print(f"\n学生姓名: {names}")
    print(f"平均分: {[f'{a:.1f}' for a in averages]}")

    # 3. 排名（按平均分降序）
    ranked = sorted(students, key=lambda s: s["average"], reverse=True)
    print("\n排名:")
    for rank, s in enumerate(ranked, start=1):
        print(f"  {rank}. {s['name']} — 平均{s['average']:.1f}")

    # 4. 统计信息
    all_scores = [score for s in students for score in s["scores"]]  # 扁平化
    print(f"\n统计:")
    print(f"  总人数: {len(students)}")
    print(f"  班级平均分: {sum(all_scores) / len(all_scores):.2f}")
    print(f"  最高单科分: {max(all_scores)}")
    print(f"  最低单科分: {min(all_scores)}")

    # 5. 按等级分组（用字典 + 列表）
    def get_grade(avg):
        """根据平均分判定等级"""
        if avg >= 90:
            return "优秀"
        elif avg >= 80:
            return "良好"
        elif avg >= 70:
            return "中等"
        elif avg >= 60:
            return "及格"
        else:
            return "不及格"

    # 用字典分组 — key是等级，value是该等级的学生列表
    groups = {}  # 初始化空字典
    for s in students:
        grade = get_grade(s["average"])
        if grade not in groups:
            groups[grade] = []  # 新等级，先创建空列表
        groups[grade].append(s["name"])

    print("\n等级分组:")
    for grade in ["优秀", "良好", "中等", "及格", "不及格"]:
        if grade in groups:
            print(f"  {grade}: {groups[grade]}")

    # 6. 导出为JSON（方便后续读写）
    export_data = [
        {"name": s["name"], "average": round(s["average"], 1)}
        for s in students
    ]
    print(f"\nJSON导出: {json.dumps(export_data, ensure_ascii=False, indent=2)}")


def main():
    """主函数 — 按顺序运行所有演示"""
    print("=" * 60)
    print("Day 03: Python数据结构与推导式")
    print("=" * 60)

    try:
        demo_list()
        demo_dict()
        demo_tuple_and_set()
        demo_comprehensions()
        demo_selection_guide()
        student_system_v2()

        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()