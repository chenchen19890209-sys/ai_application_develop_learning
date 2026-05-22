"""
生成器（Generator）深度解析 - 从底层原理到实际应用

这个文件会带您一步步理解生成器的内部工作机制
"""

# ==================== 第一部分：直观对比 ====================

print("=" * 70)
print("📊 场景1：列表 vs 生成器 - 内存占用对比")
print("=" * 70)

import sys

# 方式1：列表推导式 - 一次性把所有数据加载到内存
numbers_list = [x ** 2 for x in range(10000)]
print(f"列表占用内存: {sys.getsizeof(numbers_list)} 字节")
print(f"列表长度: {len(numbers_list)}")
print(f"前5个元素: {numbers_list[:5]}")

# 方式2：生成器表达式 - 按需生成，几乎不占内存
numbers_gen = (x ** 2 for x in range(10000))
print(f"\n生成器占用内存: {sys.getsizeof(numbers_gen)} 字节")
print(f"生成器类型: {type(numbers_gen)}")
# 注意：生成器没有 len()，因为它还没生成数据！

print("\n💡 关键区别：")
print("  列表 = 一次性做好10000个菜，全部摆在桌上（占地方）")
print("  生成器 = 现点现做，每次只做一个菜（省地方）")


# ==================== 第二部分：生成器的底层机制 ====================

print("\n" + "=" * 70)
print("🔧 场景2：生成器是如何工作的？（底层揭秘）")
print("=" * 70)

def simple_generator():
    """
    最简单的生成器函数
    
    底层发生了什么：
    1. 调用 simple_generator() 时，函数体并不执行
    2. 返回一个生成器对象（generator object）
    3. 每次调用 next() 时，函数才执行到下一个 yield
    4. yield 会"暂停"函数，保存当前状态，返回值
    5. 下次调用 next() 时，从上次暂停的地方继续
    """
    print("  → 开始执行，准备产生第1个值")
    yield 1
    print("  → 恢复执行，准备产生第2个值")
    yield 2
    print("  → 恢复执行，准备产生第3个值")
    yield 3
    print("  → 执行完毕")

# 创建生成器对象（此时函数体还没有执行！）
gen = simple_generator()
print(f"生成器对象: {gen}")
print(f"生成器状态: 已创建，但未执行")

# 第一次调用 next()
print("\n第1次 next():")
value1 = next(gen)
print(f"  得到值: {value1}")

# 第二次调用 next()
print("\n第2次 next():")
value2 = next(gen)
print(f"  得到值: {value2}")

# 第三次调用 next()
print("\n第3次 next():")
value3 = next(gen)
print(f"  得到值: {value3}")

# 第四次调用 next() - 会抛出 StopIteration 异常
print("\n第4次 next():")
try:
    value4 = next(gen)
except StopIteration:
    print("  ❌ StopIteration 异常：生成器已耗尽")


# ==================== 第三部分：手动模拟生成器的工作原理 ====================

print("\n" + "=" * 70)
print("🎭 场景3：手动实现一个'类生成器'（帮助理解底层）")
print("=" * 70)

class ManualGenerator:
    """
    手动模拟生成器的工作原理
    
    真正的生成器在C层面实现了类似的功能，
    但这里是Python层面的简化版本
    """
    
    def __init__(self, n):
        self.n = n
        self.current = 0
        self.state = "initialized"  # 记录当前状态
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.current >= self.n:
            raise StopIteration
        
        # 计算当前值
        value = self.current ** 2
        
        # 更新状态（模拟yield后的暂停）
        self.current += 1
        self.state = f"suspended at {self.current}"
        
        return value

# 使用手动实现的生成器
print("手动实现的生成器:")
manual_gen = ManualGenerator(5)
for value in manual_gen:
    print(f"  得到值: {value}, 状态: {manual_gen.state}")


# ==================== 第四部分：生成器的状态机本质 ====================

print("\n" + "=" * 70)
print("🔄 场景4：生成器本质上是一个状态机")
print("=" * 70)

def state_machine_generator():
    """
    展示生成器的状态转换
    
    状态变化：
    Created → Running → Suspended → Running → Suspended → ... → Closed
    """
    print("  [状态: Running] 初始化变量")
    x = 0
    
    print("  [状态: Running] 第1次循环")
    x += 1
    yield x  # 暂停在这里，保存 x=1
    
    print("  [状态: Running] 第2次循环")
    x += 2
    yield x  # 暂停在这里，保存 x=3
    
    print("  [状态: Running] 第3次循环")
    x += 3
    yield x  # 暂停在这里，保存 x=6
    
    print("  [状态: Running] 函数结束")

gen = state_machine_generator()
print("创建生成器（状态: Created）")

for i in range(4):
    try:
        print(f"\n第{i+1}次调用 next():")
        value = next(gen)
        print(f"  [状态: Suspended] 返回值: {value}")
    except StopIteration:
        print(f"  [状态: Closed] 生成器已结束")
        break


# ==================== 第五部分：生成器的高级特性 ====================

print("\n" + "=" * 70)
print("⚡ 场景5：生成器的高级功能 - send() 和 close()")
print("=" * 70)

def interactive_generator():
    """
    可以接收外部输入的生成器
    
    yield 不仅可以返回值，还可以接收值！
    """
    print("  生成器启动")
    
    # 第1个yield：只能接收None（启动时）
    received = yield "ready"
    print(f"  收到: {received}")
    
    # 第2个yield：可以接收send()发送的值
    received = yield "waiting"
    print(f"  收到: {received}")
    
    # 第3个yield
    received = yield "done"
    print(f"  收到: {received}")

gen = interactive_generator()

# 启动生成器（必须先用 None 启动）
print("启动生成器:")
result = next(gen)
print(f"  得到: {result}")

# 使用 send() 发送值
print("\n发送 'hello':")
result = gen.send("hello")
print(f"  得到: {result}")

print("\n发送 'world':")
result = gen.send("world")
print(f"  得到: {result}")

# 提前关闭生成器
print("\n关闭生成器:")
gen.close()
print("  生成器已关闭")


# ==================== 第六部分：实际应用场景 ====================

print("\n" + "=" * 70)
print("🌍 场景6：生成器的实际应用")
print("=" * 70)

# 应用1：处理大文件（逐行读取，不一次性加载）
print("\n【应用1】处理大文件")
def read_large_file(file_path):
    """
    逐行读取大文件，而不是一次性加载到内存
    
    适合处理GB级别的日志文件、CSV文件等
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            yield line.strip()

# 创建一个测试文件
test_file = "test_large_file.txt"
with open(test_file, 'w', encoding='utf-8') as f:
    for i in range(1000):
        f.write(f"这是第{i+1}行数据\n")

print(f"  创建测试文件: {test_file} (1000行)")
print("  逐行读取（每次只加载一行）:")

line_count = 0
for line in read_large_file(test_file):
    line_count += 1
    if line_count <= 3:
        print(f"    {line}")
    elif line_count == 4:
        print("    ...")

print(f"  总共读取了 {line_count} 行")


# 应用2：无限序列生成器
print("\n【应用2】无限序列")
def fibonacci():
    """
    生成斐波那契数列（无限）
    
    因为生成器是惰性的，所以可以表示无限序列
    """
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

fib_gen = fibonacci()
print("  斐波那契数列前10个数:")
fib_numbers = [next(fib_gen) for _ in range(10)]
print(f"  {fib_numbers}")


# 应用3：数据管道（链式处理）
print("\n【应用3】数据管道")
def generate_numbers(n):
    """生成0到n-1的数字"""
    for i in range(n):
        yield i

def filter_even(numbers):
    """只保留偶数"""
    for num in numbers:
        if num % 2 == 0:
            yield num

def square_numbers(numbers):
    """计算平方"""
    for num in numbers:
        yield num ** 2

# 链式组合：生成 → 过滤 → 转换
pipeline = square_numbers(filter_even(generate_numbers(10)))
print("  0-9中的偶数的平方:")
print(f"  {list(pipeline)}")  # [0, 4, 16, 36, 64]


# 应用4：分批处理数据
print("\n【应用4】分批处理")
def batch_processor(data, batch_size):
    """
    将数据分批处理
    
    在AI训练中很常用：批量处理数据
    """
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]

data = list(range(25))
batches = batch_processor(data, batch_size=5)

print("  将25个数据分成5批:")
for i, batch in enumerate(batches, 1):
    print(f"    批次{i}: {batch}")


# ==================== 第七部分：性能对比实验 ====================

print("\n" + "=" * 70)
print("📈 场景7：性能对比 - 列表 vs 生成器")
print("=" * 70)

import time

# 测试1：创建时间
print("\n【测试1】创建100万元素")

start = time.time()
large_list = [x ** 2 for x in range(1_000_000)]
list_time = time.time() - start
print(f"  列表创建时间: {list_time:.4f}秒")
print(f"  列表内存占用: {sys.getsizeof(large_list) / 1024 / 1024:.2f}MB")

start = time.time()
large_gen = (x ** 2 for x in range(1_000_000))
gen_time = time.time() - start
print(f"  生成器创建时间: {gen_time:.6f}秒")
print(f"  生成器内存占用: {sys.getsizeof(large_gen) / 1024:.2f}KB")

# 测试2：遍历时间
print("\n【测试2】遍历求和")

start = time.time()
list_sum = sum(large_list)
list_sum_time = time.time() - start
print(f"  列表求和时间: {list_sum_time:.4f}秒")

start = time.time()
gen_sum = sum(large_gen)
gen_sum_time = time.time() - start
print(f"  生成器求和时间: {gen_sum_time:.4f}秒")

print(f"\n  结果相同: {list_sum == gen_sum}")
print(f"  求和结果: {list_sum:,}")


# ==================== 第八部分：常见陷阱 ====================

print("\n" + "=" * 70)
print("⚠️ 场景8：生成器的常见陷阱")
print("=" * 70)

# 陷阱1：生成器只能遍历一次
print("\n【陷阱1】生成器只能使用一次")
gen = (x ** 2 for x in range(5))
print(f"  第1次遍历: {list(gen)}")
print(f"  第2次遍历: {list(gen)}")  # 空列表！
print("  💡 原因：生成器已经耗尽了")

# 陷阱2：生成器表达式中的变量作用域
print("\n【陷阱2】生成器表达式的延迟绑定")
x = 10
gen = (x * i for i in range(5))
x = 20  # 修改x的值
print(f"  结果: {list(gen)}")  # [0, 20, 40, 60, 80] 而不是 [0, 10, 20, 30, 40]
print("  💡 原因：生成器在迭代时才读取x的值")

# 陷阱3：生成器不能获取长度
print("\n【陷阱3】生成器没有len()")
gen = (x for x in range(100))
try:
    length = len(gen)
except TypeError as e:
    print(f"  错误: {e}")
    print("  💡 解决：先转换为列表 list(gen)，但这会消耗生成器")


# ==================== 总结 ====================

print("\n" + "=" * 70)
print("🎯 生成器核心要点总结")
print("=" * 70)
print("""
1. 生成器是什么？
   → 一种特殊的迭代器，按需生成数据

2. 底层原理：
   → 状态机：保存执行状态，每次从暂停处继续
   → yield 关键字：暂停函数，返回值
   → next() 函数：恢复执行，获取下一个值

3. 为什么省内存？
   → 列表：一次性生成所有数据 → O(n) 内存
   → 生成器：一次只生成一个数据 → O(1) 内存

4. 何时使用生成器？
   ✓ 处理大数据集（文件、数据库查询）
   ✓ 无限序列（斐波那契、随机数）
   ✓ 数据管道（流式处理）
   ✓ 需要惰性求值的场景

5. 何时不使用生成器？
   ✗ 需要多次遍历数据
   ✗ 需要随机访问（如 gen[5]）
   ✗ 需要知道数据长度
   ✗ 数据量很小（ overhead 可能更大）

6. 记住这个比喻：
   列表 = 自助餐（所有菜都摆好了）
   生成器 = 点餐制（现点现做）
""")

# 清理测试文件
import os
if os.path.exists(test_file):
    os.remove(test_file)
    print(f"\n✅ 已清理测试文件: {test_file}")
