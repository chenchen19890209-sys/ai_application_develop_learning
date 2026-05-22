"""
functions_demo.py
Python函数、模块与高级特性综合演示

功能：
1. 函数定义与参数传递（*args, **kwargs）
2. lambda匿名函数
3. 类型提示（Type Hints）
4. 装饰器（计时器、重试、缓存）
5. 生成器（Generator）
6. 模块导入机制

学习目标：
1. 掌握函数的各种参数传递方式
2. 理解装饰器的原理并能自定义装饰器
3. 学会用生成器处理大数据
4. 了解类型提示在AI开发中的重要性
"""
import time  # 计时器装饰器
from functools import wraps  # 保留被装饰函数的元信息
from typing import List, Dict, Optional, Callable, Generator  # 类型提示


# ==================== 第1部分：函数定义与参数 ====================

def demo_functions():
    """演示函数的各种定义和调用方式"""
    print("=" * 50)
    print("📋 1. 函数定义与参数")
    print("-" * 50)

    # 基本函数 — 有参数有返回值
    def greet(name: str) -> str:
        """向指定的人打招呼（带类型提示）"""
        return f"你好，{name}！"

    print(f"基本函数: {greet('学习者')}")

    # 默认参数 — 调用时可省略，使用默认值
    def greet_formal(name: str, greeting: str = "你好") -> str:
        """带默认问候语的函数"""
        return f"{greeting}，{name}！"

    print(f"默认参数(省略): {greet_formal('张三')}")
    print(f"默认参数(指定): {greet_formal('李四', 'Good morning')}")

    # *args — 接收任意数量的位置参数，在函数内部是一个元组
    def sum_all(*args: float) -> float:
        """计算任意数量数值的总和"""
        return sum(args)

    print(f"*args (3个): {sum_all(1, 2, 3)} = {1 + 2 + 3}")
    print(f"*args (5个): {sum_all(1, 2, 3, 4, 5)} = {1 + 2 + 3 + 4 + 5}")

    # **kwargs — 接收任意数量的关键字参数，在函数内部是一个字典
    def build_config(**kwargs) -> Dict:
        """构建配置字典"""
        # 设置默认值，用用户提供的值覆盖
        defaults = {"debug": False, "log_level": "INFO"}
        defaults.update(kwargs)  # update用提供的值覆盖默认值
        return defaults

    config = build_config(debug=True, database="postgresql")
    print(f"**kwargs: {config}")

    # 解包操作 — 用 * 把列表/元组拆成位置参数，用 ** 把字典拆成关键字参数
    numbers = [3, 1, 4, 1, 5]
    print(f"解包列表: sum(*numbers) = {sum_all(*numbers)}")

    params = {"debug": True, "log_level": "DEBUG", "host": "localhost"}
    print(f"解包字典: {build_config(**params)}")


# ==================== 第2部分：lambda表达式 ====================

def demo_lambda():
    """演示lambda匿名函数的用法"""
    print("\n" + "=" * 50)
    print("📋 2. lambda匿名函数")
    print("-" * 50)

    # lambda 语法: lambda 参数: 返回值表达式
    # 等价于 def add(x, y): return x + y
    add = lambda x, y: x + y
    print(f"lambda加法: 3+5 = {add(3, 5)}")

    # lambda vs def — lambda适合简短的、用完即扔的操作
    # 主要用法1: sorted/max/min的key参数
    students = [
        {"name": "张三", "score": 85},
        {"name": "李四", "score": 92},
        {"name": "王五", "score": 78},
    ]
    # 按成绩排序
    sorted_by_score = sorted(students, key=lambda s: s["score"])
    print(f"按成绩排序: {[s['name'] for s in sorted_by_score]}")

    # 主要用法2: map()
    numbers = [1, 2, 3, 4, 5]
    squared = list(map(lambda x: x ** 2, numbers))  # map返回迭代器，list()转列表
    print(f"map平方: {squared}")

    # 主要用法3: filter()
    evens = list(filter(lambda x: x % 2 == 0, numbers))
    print(f"filter偶数: {evens}")


# ==================== 第3部分：类型提示 ====================

def demo_type_hints():
    """演示Type Hints（类型提示）的用法和价值"""
    print("\n" + "=" * 50)
    print("📋 3. 类型提示（Type Hints）")
    print("-" * 50)

    # Python是动态类型语言，但可以加类型提示提高可读性
    # ⚠️ 类型提示不影响运行时行为，只用于文档和IDE检查

    def calculate_average(scores: List[float]) -> float:
        """计算平均分 — 参数是float列表，返回float"""
        if not scores:  # 空列表处理
            return 0.0
        return sum(scores) / len(scores)

    scores: List[float] = [85.5, 90.0, 78.5]
    average: float = calculate_average(scores)
    print(f"平均分: {average:.2f}")

    # 复杂类型：Optional表示可以是None
    def find_student(name: str, students: List[Dict]) -> Optional[Dict]:
        """查找学生，返回Dict或None"""
        for s in students:
            if s["name"] == name:
                return s
        return None  # Optional允许返回None

    students: List[Dict] = [
        {"name": "张三", "age": 20, "score": 85},
        {"name": "李四", "age": 21, "score": 92},
        {"name": "王五", "age": 22, "score": 78}
    ]
    result = find_student("李四", students)
    print(f"查找结果: {result['name'] if result else '未找到'}")

    # Callable类型 — 表示函数类型
    def apply_function(func: Callable[[float], float], value: float) -> float:
        """对value应用func — func接收float返回float"""
        return func(value)

    print(f"应用sqrt: {apply_function(lambda x: x ** 0.5, 16.0)}")

    # ⚠️ Type Hints在AI开发中的特殊价值：
    # LLM的Function Calling / Tool Use机制会从类型提示生成JSON Schema！
    print("\n💡 AI开发提示：LLM的函数调用功能会从Type Hints推导参数类型！")
    print("  def search(query: str, limit: int = 10) -> List[Dict]:")
    print("  → 自动生成JSON Schema: {query: {type: string}, limit: {type: integer}}")


# ==================== 第4部分：装饰器 ====================

def demo_decorators():
    """演示装饰器的原理和实际应用"""
    print("\n" + "=" * 50)
    print("📋 4. 装饰器（Decorator）")
    print("-" * 50)

    # 手动理解装饰器原理（不用@语法糖的情况下）
    def timer_manual(func):
        """装饰器函数：接收函数，返回包装后的函数"""
        @wraps(func)  # 保留原函数的名称和文档字符串
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            print(f"  {func.__name__} 耗时: {elapsed:.3f}秒")
            return result
        return wrapper

    @timer_manual
    def slow_operation():
        """模拟一个耗时的操作"""
        time.sleep(0.5)
        return "操作完成"

    print("调用 @timer_manual 装饰的函数:")
    result = slow_operation()
    print(f"  返回: {result}")

    # 装饰器2: 重试装饰器
    def retry(max_attempts: int = 3, delay: float = 0.2):
        """重试装饰器 — 带参数的装饰器（三层嵌套）"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(1, max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_attempts:
                            print(f"  ❌ 重试{max_attempts}次后仍然失败: {e}")
                            raise  # 最后一次重试失败，抛出异常
                        print(f"  ⚠️ 第{attempt}次失败: {e}，{delay}秒后重试...")
                        time.sleep(delay)
                return None
            return wrapper
        return decorator

    # 模拟一个不稳定的函数：前几次调用会失败
    call_count = {"count": 0}  # 用字典避免nonlocal

    @retry(max_attempts=3, delay=0.1)
    def unstable_function():
        """模拟不稳定的API调用"""
        call_count["count"] += 1
        if call_count["count"] < 3:
            raise ConnectionError("网络连接失败")
        return "API调用成功"

    print(f"\n调用 @retry(3) 装饰的函数（前2次会失败）:")
    result = unstable_function()
    print(f"  最终返回: {result}")

    # 装饰器3: 缓存装饰器（Memoization）
    def memoize(func):
        """简单的缓存装饰器 — 用字典存储已计算的结果"""
        cache = {}  # 闭包变量存储缓存

        @wraps(func)
        def wrapper(*args):
            if args not in cache:
                cache[args] = func(*args)  # 首次计算并缓存
                print(f"  计算 {args} = {cache[args]}（已缓存）")
            else:                print(f"  命中缓存 {args} = {cache[args]}")
            return cache[args]

        return wrapper

    @memoize
    def fibonacci(n: int) -> int:
        """计算斐波那契数（递归，慢）"""
        if n <= 1:
            return n
        return fibonacci(n - 1) + fibonacci(n - 2)

    print(f"\nFibonacci(10) 使用缓存装饰器:")
    result = fibonacci(10)
    print(f"  结果: {result}")


# ==================== 第5部分：生成器 ====================

def demo_generators():
    """演示生成器（Generator）的原理和应用"""
    print("\n" + "=" * 50)
    print("📋 5. 生成器（Generator）")
    print("-" * 50)

    # 生成器用yield按需生成数据，而不是一次性创建所有数据
    # 对比：列表 vs 生成器

    # 传统方式 — 一次性创建一个1千万元素的列表（大内存！）
    # big_list = [x ** 2 for x in range(10_000_000)]  # 约80MB！

    # 生成器方式 — 内存中同时只有当前元素
    # big_gen = (x ** 2 for x in range(10_000_000))  # 几乎不占内存！

    # 生成器函数 — 用yield代替return
    def countdown(n: int):
        """倒计时生成器"""
        print(f"倒计时开始（从{n}）...")
        while n > 0:
            yield n  # yield暂停函数，返回当前值
            n -= 1
        print("倒计时结束！")
        # 函数结束 = 生成器耗尽

    print("倒计时生成器:")
    for num in countdown(3):
        print(f"  {num}...")

    # 惰性求值 — 每一个yield之间可以执行大量代码
    def read_large_file_in_batches(filepath: str, batch_size: int = 2):
        """模拟逐批读取大文件（实际开发中用于处理超大数据集）"""
        # 模拟大文件的内容
        lines = ["行1: 数据A", "行2: 数据B", "行3: 数据C", "行4: 数据D", "行5: 数据E"]
        batch = []
        for i, line in enumerate(lines, 1):
            batch.append(line)
            if len(batch) == batch_size or i == len(lines):
                yield batch  # 攒够一批就yield
                batch = []  # 清空，准备下一批

    print("\n逐批读取:")
    for batch in read_large_file_in_batches("large_file.txt", batch_size=2):
        print(f"  批次: {batch}")

    # 生成器管道 — 组合多个生成器
    def generate_numbers(n: int):
        """生成器1: 产生数字"""
        for i in range(n):
            yield i

    def square_numbers(numbers):
        """生成器2: 对数字求平方"""
        for num in numbers:
            yield num ** 2

    def filter_even(numbers):
        """生成器3: 过滤偶数"""
        for num in numbers:
            if num % 2 == 0:
                yield num

    # 构建管道：产生数字 → 平方 → 过滤偶数
    print("\n生成器管道（0-9 → 平方 → 过滤偶数）:")
    pipeline = filter_even(square_numbers(generate_numbers(10)))
    print(f"  结果: {list(pipeline)}")


# ==================== 第6部分：模块导入机制 ====================

def demo_imports():
    """演示模块导入机制和__name__ == '__main__'"""
    print("\n" + "=" * 50)
    print("📋 6. 模块导入机制")
    print("-" * 50)

    print(f"当前模块的 __name__ = {__name__!r}")
    print(f"如果是直接运行的: __name__ == '__main__'")
    print(f"如果是被import的: __name__ == 'functions_demo'")

    # 演示：显示Python查找模块的路径
    import sys
    print(f"\nsys.path 前3项:")
    for p in sys.path[:3]:
        print(f"  {p}")

    print("\n💡 导入路径参考（新课程结构）:")
    print("  from config import OPENAI_API_KEY")
    print("  # Project root must be in sys.path")


def main():
    """主函数 — 按顺序运行所有演示"""
    print("=" * 60)
    print("Day 04: Python函数、模块与高级特性")
    print("=" * 60)

    try:
        demo_functions()
        demo_lambda()
        demo_type_hints()
        demo_decorators()
        demo_generators()
        demo_imports()

        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()